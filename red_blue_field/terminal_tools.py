"""Role-limited local REST adapters. The model never receives controller credentials."""
from __future__ import annotations

import asyncio

import httpx
from langchain_core.tools import tool

from .models import Action
from .tools import CASE_TOOLS, TOOL_DESCRIPTIONS


def build_tools(role, run_id, client: httpx.AsyncClient, log, allowed):
    base = '/api/runs/' + run_id
    last_seen = set()
    action_lock = asyncio.Lock()
    proposed = None

    @tool
    async def lab_context() -> dict:
        """Describe only this episode, its status, scope and allowed tool arguments."""
        response = await client.get(base)
        response.raise_for_status()
        value = response.json()
        sid = value['scenario_id']
        return {'run_id': run_id, 'scenario_id': sid, 'profile': value['profile'], 'status': value['status'],
                'environment': value['context']['environment_kind'], 'mode': value['request']['mode'],
                'allowed_actions': {name: TOOL_DESCRIPTIONS[name] for name in sorted(CASE_TOOLS[sid])} if role == 'red' else {},
                'actions_enabled': allowed(), 'closed': value['status'] in {'complete', 'interrupted', 'invalid'}}

    @tool
    async def propose_test(name: str, arguments: dict, claim: str, falsification: str, parent_id: str | None = None) -> dict:
        """Queue an episode-scoped hypothesis with evidence criterion; never execute it."""
        nonlocal proposed
        async with action_lock:
            action = Action(name=name, arguments=arguments, reason=claim)
            response = await client.post(base + '/hypotheses', json={'action': action.model_dump(), 'claim': claim,
                                                                    'falsification': falsification, 'parent_id': parent_id})
            node = response.json().get('node')
            proposed = node['hypothesis_id'] if node and node['status'] == 'proposed' else None
            return {'http_status': response.status_code, 'result': response.json()}

    @tool
    async def execute_next_test() -> dict:
        """Execute ONE queued hypothesis, only after the operator enables actions."""
        nonlocal proposed
        async with action_lock:
            if not allowed():
                return {'denied': 'Operator must enable actions with /allow or --allow-actions'}
            if not proposed:
                return {'denied': 'Propose a hypothesis in this chat before executing it'}
            response = await client.post(base + '/step', json={'expected_hypothesis_id': proposed})
            if response.is_success and response.json().get('status') != 'waiting_review':
                proposed = None
            # Return observations from the executed action, not the hidden evaluator state.
            events = await client.get(base + '/events')
            events.raise_for_status()
            visible = [e for e in events.json() if e['event_type'] in {'tool.executed', 'policy.evaluated', 'approval.requested'}]
            return {'http_status': response.status_code, 'status': response.json().get('status'), 'events': visible[-8:]}

    @tool
    async def observe_events(after: int = -1) -> dict:
        """Read authenticated gateway and blue signals, excluding private evaluator state."""
        response = await client.get(base + '/events', params={'after': after})
        response.raise_for_status()
        # Proposals and evaluator decisions are not blue detection evidence.
        visible = [e for e in response.json() if e['actor'] in {'tool', 'target', 'policy', 'blue'}]
        window = visible[:30]
        for event in window:
            last_seen.add(event['sequence'])
        return {'events': window, 'next_after': window[-1]['sequence'] if window else max([after, *[e['sequence'] for e in response.json()]]),
                'has_more': len(visible) > len(window)}

    @tool
    async def contain(response: str, reason: str, evidence_sequences: list[int]) -> dict:
        """Apply an allowed blue response, bound to observed event sequences and operator consent."""
        async with action_lock:
            if response not in {'observe', 'quarantine_document', 'suspend_tool', 'revoke_session', 'restore'}:
                return {'denied': 'Response outside blue capabilities'}
            if not evidence_sequences or not set(evidence_sequences) <= last_seen:
                return {'denied': 'Observe the referenced events before containment'}
            if not allowed():
                return {'denied': 'Operator must enable actions with /allow or --allow-actions'}
            result = await client.post(base + '/blue', json={'response': response, 'reason': reason,
                'actor': 'external_agent', 'external_session_id': log.id, 'evidence_sequences': evidence_sequences})
            return {'http_status': result.status_code, 'result': result.json()}

    return [lab_context, propose_test, execute_next_test] if role == 'red' else [lab_context, observe_events, contain]
