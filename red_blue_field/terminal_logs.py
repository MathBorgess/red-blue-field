"""Private per-terminal audit logs, including the actual native Responses payload."""
from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from pathlib import Path

import httpx

from .evidence import atomic_json, canonical, digest, now


class SessionLog:
    def __init__(self, root: Path, role: str, run_id: str, model: str, secrets: list[str], *, max_calls=40, max_tokens=100000):
        self.id = uuid.uuid4().hex
        self.root = root / role / self.id
        self.root.mkdir(parents=True, mode=0o700)
        self.root.chmod(0o700)
        self.secrets = [value for value in secrets if value]
        self.sequence, self.last_hash = 0, None
        self.max_calls, self.max_tokens = max_calls, max_tokens
        self.started = time.monotonic()
        self.echo = False
        self.metrics = dict(session_id=self.id, run_id=run_id, role=role, model=model, provider='codex_proxy',
                            provider_execution='not_observed', model_calls=0, model_responses=0, input_tokens=0,
                            output_tokens=0, cached_input_tokens=0, unknown_usage_calls=0, tool_calls=0,
                            tool_denials=0, model_latency_ms=[], turns=0, errors=0, cost_usd=None,
                            cost_status='not_reported_by_subscription_proxy', status='open')

    def clean(self, value):
        if isinstance(value, dict):
            if value.get('type') in {'reasoning', 'thinking', 'redacted_thinking'}:
                return {'type': value['type'], 'content': '[private reasoning omitted]'}
            return {k: '[redacted]' if k.lower() in {'authorization', 'api_key', 'access_token', 'refresh_token', 'encrypted_content'} else self.clean(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [self.clean(v) for v in value]
        if isinstance(value, str):
            for secret in self.secrets:
                value = value.replace(secret, '[redacted]')
            return value
        return value

    def event(self, kind: str, payload: dict):
        event = dict(session_id=self.id, run_id=self.metrics['run_id'], role=self.metrics['role'], sequence=self.sequence,
                     occurred_at=now(), event_type=kind, payload=self.clean(payload), prev_event_hash=self.last_hash)
        event['event_hash'] = digest(event)
        fd = os.open(self.root / 'events.jsonl', os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, 'ab') as handle:
            handle.write(canonical(event) + b'\n')
            handle.flush()
            os.fsync(handle.fileno())
        self.last_hash, self.sequence = event['event_hash'], self.sequence + 1
        self.save()
        if self.echo:
            if kind == 'model.requested':
                print(f"[modelo #{payload['call']}] pedido Responses; prompt e schemas em latest-request.json")
            elif kind == 'model.responded':
                print(f"[modelo #{payload['call']}] HTTP {payload['http_status']}; {payload['latency_ms']:.0f} ms; usage={payload['usage']}")
            elif kind.startswith('tool.') or kind == 'plan.updated':
                print('[' + kind + '] ' + json.dumps(event['payload'], ensure_ascii=False)[:1200])

    def save(self):
        self.metrics['elapsed_ms'] = (time.monotonic() - self.started) * 1000
        self.metrics['last_event_hash'] = self.last_hash
        self.metrics['unanswered_model_calls'] = self.metrics['model_calls'] - self.metrics['model_responses']
        atomic_json(self.root / 'metrics.json', self.metrics)
        (self.root / 'metrics.json').chmod(0o600)

    async def request(self, request: httpx.Request):
        payload = json.loads(request.content)
        if any(secret in json.dumps(payload, ensure_ascii=False) for secret in self.secrets):
            self.event('credential.blocked', {'reason': 'Application credential found in provider input'})
            raise RuntimeError('Application credentials cannot be sent to the model')
        # The cap stops the NEXT call; missing usage never becomes a fabricated zero charge.
        if self.metrics['model_calls'] >= self.max_calls or self.metrics['input_tokens'] + self.metrics['output_tokens'] >= self.max_tokens:
            self.event('budget.denied', {'max_calls': self.max_calls, 'max_reported_tokens': self.max_tokens})
            raise RuntimeError('Chat model budget exhausted')
        request.extensions['rbf_started'] = time.monotonic()
        self.metrics['model_calls'] += 1
        request.extensions['rbf_call'] = self.metrics['model_calls']
        self.event('model.requested', {'call': self.metrics['model_calls'], 'protocol': 'responses',
                   'body_sha256': hashlib.sha256(request.content).hexdigest(), 'body': payload})
        atomic_json(self.root / 'latest-request.json', self.clean(payload))
        (self.root / 'latest-request.json').chmod(0o600)

    async def response(self, response: httpx.Response):
        await response.aread()
        elapsed = (time.monotonic() - response.request.extensions['rbf_started']) * 1000
        try:
            payload = response.json()
        except ValueError:
            payload = {'format': 'non_json_response', 'body_bytes': len(response.content)}
        self.metrics['model_responses'] += 1
        self.metrics['model_latency_ms'].append(elapsed)
        self.metrics['provider_execution'] = 'responses_observed' if response.is_success else 'provider_error_observed'
        usage = payload.get('usage') or {}
        if isinstance(usage.get('input_tokens'), int) and isinstance(usage.get('output_tokens'), int):
            self.metrics['input_tokens'] += max(0, usage['input_tokens'])
            self.metrics['output_tokens'] += max(0, usage['output_tokens'])
            self.metrics['cached_input_tokens'] += max(0, (usage.get('input_tokens_details') or {}).get('cached_tokens', 0))
        else:
            self.metrics['unknown_usage_calls'] += 1
        if not response.is_success:
            self.metrics['errors'] += 1
        self.event('model.responded', {'call': response.request.extensions.get('rbf_call'), 'http_status': response.status_code,
                                      'latency_ms': elapsed, 'usage': usage, 'body': payload})
        atomic_json(self.root / 'latest-response.json', self.clean(payload))
        (self.root / 'latest-response.json').chmod(0o600)

    def close(self, status='closed'):
        self.metrics['status'] = status
        self.event('session.finished', {'status': status})
