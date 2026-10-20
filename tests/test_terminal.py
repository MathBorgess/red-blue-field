import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
from argparse import ArgumentTypeError
from argparse import Namespace
from pathlib import Path

import httpx
import pytest
import uvicorn
from fastapi import FastAPI, Request

pytest.importorskip('deepagents')
from langchain_openai import ChatOpenAI
from red_blue_field.evidence import digest, verify_export
from red_blue_field.models import RunRequest
from red_blue_field.models import Action
from red_blue_field.terminal import build_agent, loopback_url
from red_blue_field.terminal_logs import SessionLog
from red_blue_field.terminal_tools import build_tools


def tool_call(name, arguments, counter):
    return {'type': 'function_call', 'id': f'fc_{counter}', 'call_id': f'call_{counter}', 'name': name, 'arguments': json.dumps(arguments), 'status': 'completed'}


def completed(output, counter):
    return {'id': f'resp_{counter}', 'object': 'response', 'created_at': 1, 'status': 'completed', 'model': 'test-codex-model',
            'output': output, 'usage': {'input_tokens': 40, 'output_tokens': 10, 'total_tokens': 50, 'input_tokens_details': {'cached_tokens': 5}}}


def final():
    return {'type': 'message', 'id': 'msg_end', 'role': 'assistant', 'status': 'completed', 'content': [{'type': 'output_text', 'text': 'Resultado observado no laboratório.', 'annotations': []}]}


@pytest.mark.parametrize('url', ['https://example.com/v1', 'http://127.0.0.1.evil.invalid/v1', 'http://user:secret@localhost/v1', 'http://localhost/v1?token=secret', 'file:///tmp/model'])
def test_chats_only_connect_to_explicit_loopback(url):
    with pytest.raises(ArgumentTypeError):
        loopback_url(url)


async def test_two_real_deep_agents_native_responses_and_role_tools(app, client, tmp_path):
    lab = app.state.lab
    run = await lab.create(RunRequest(scenario_id='S01', profile='A', mode='manual'))
    all_logs = []
    for role in ['red', 'blue']:
        log = SessionLog(tmp_path / 'chats', role, run.id, 'test-codex-model', [lab.settings.control_token])
        all_logs.append(log)
        tools = build_tools(role, run.id, client, log, lambda: True)
        counter = 0
        async def provider(request):
            nonlocal counter
            assert request.url.path == '/v1/responses'
            body = json.loads(request.content)
            assert body['store'] is False
            assert body.get('stream') is False
            assert lab.settings.control_token not in request.content.decode()
            names = {tool['name'] for tool in body['tools']}
            assert not names & {'task', 'execute', 'system_inspect', 'python_eval'}
            assert ('propose_test' in names) == (role == 'red')
            assert ('contain' in names) == (role == 'blue')
            counter += 1
            if counter == 1:
                output = tool_call('write_todos', {'todos': [{'content': 'Testar a hipótese com evidência do alvo', 'status': 'in_progress'}]}, counter)
            elif counter == 2:
                output = tool_call('lab_context' if role == 'red' else 'observe_events', {}, counter)
            elif counter == 3:
                if role == 'red':
                    output = tool_call('propose_test', {'name': 'read_ticket', 'arguments': {'ticket_id': 'ticket-beta'},
                        'claim': 'A autorização pode aceitar acesso entre clientes', 'falsification': 'O servidor nega a leitura do outro cliente'}, counter)
                else:
                    sequence = next(e['sequence'] for e in run.collector.events if e['event_type'] == 'tool.executed')
                    output = tool_call('contain', {'response': 'revoke_session', 'reason': 'Leitura entre clientes confirmada no evento do gateway', 'evidence_sequences': [sequence]}, counter)
            elif counter == 4 and role == 'red':
                output = tool_call('execute_next_test', {}, counter)
            else:
                output = final()
            return httpx.Response(200, json=completed([output], counter))
        async with httpx.AsyncClient(transport=httpx.MockTransport(provider), event_hooks={'request': [log.request], 'response': [log.response]}) as proxy:
            model = ChatOpenAI(model='test-codex-model', base_url='http://localhost/v1', api_key='local-proxy', use_responses_api=True,
                store=False, max_retries=0, http_async_client=proxy, http_socket_options=(), streaming=False, model_kwargs={'parallel_tool_calls': False})
            agent, boundary = build_agent(role, model, tools, log, 'Estude o episódio sintético e explique suas observações.')
            state = await agent.ainvoke({'messages': [{'role': 'user', 'content': 'Execute o experimento permitido.'}]},
                                       config={'configurable': {'thread_id': log.id}, 'recursion_limit': 40})
            assert 'Resultado observado' in state['messages'][-1].text
            assert state['todos']
        log.close()
        assert log.metrics['model_calls'] == counter
        assert log.metrics['input_tokens'] == counter * 40
        assert log.metrics['output_tokens'] == counter * 10
        assert log.metrics['cost_usd'] is None
        events = [json.loads(line) for line in (log.root / 'events.jsonl').read_text().splitlines()]
        assert any(e['event_type'] == 'plan.updated' for e in events)
        previous = None
        for index, event in enumerate(events):
            assert event['sequence'] == index
            assert event['prev_event_hash'] == previous
            assert digest({k:v for k,v in event.items() if k != 'event_hash'}) == event['event_hash']
            previous = event['event_hash']
    assert all_logs[0].root != all_logs[1].root
    assert any(e['kind'] == 'cross_tenant_read' for e in run.fixture.snapshot()['effects'])
    assert run.fixture.state('session_revoked') is True
    response = next(e for e in run.collector.events if e['event_type'] == 'blue.response')
    assert response['payload']['human_operator'] is False
    assert response['payload']['external_session_id'] == all_logs[1].id
    await lab.finish(run, 'completed')
    assert verify_export(run.collector.root)['valid']


async def test_read_only_and_blue_evidence_gate(app, client, tmp_path):
    run = await app.state.lab.create(RunRequest(mode='manual'))
    for role in ['red', 'blue']:
        log = SessionLog(tmp_path, role, run.id, 'test-model', [])
        tools = {t.name: t for t in build_tools(role, run.id, client, log, lambda: False)}
        if role == 'red':
            assert 'denied' in await tools['execute_next_test'].ainvoke({})
        else:
            assert 'denied' in await tools['contain'].ainvoke({'response': 'restore', 'reason': 'Synthetic test', 'evidence_sequences': [999]})
    assert run.fixture.snapshot()['effects'] == []
    bad = await client.post(f'/api/runs/{run.id}/blue', json={'response': 'restore', 'reason': 'Synthetic test', 'actor': 'external_agent', 'external_session_id': 'a'*32, 'evidence_sequences': [999]})
    assert bad.status_code == 422


async def test_log_redaction_and_unknown_usage(tmp_path):
    log = SessionLog(tmp_path, 'red', 'a'*32, 'test-model', ['CONTROL_SECRET'])
    async def provider(request):
        return httpx.Response(200, json=completed([{'type': 'reasoning', 'summary': [{'text': 'private reasoning must be omitted'}]}, final()], 1) | {'usage': None})
    async with httpx.AsyncClient(transport=httpx.MockTransport(provider), event_hooks={'request': [log.request], 'response': [log.response]}) as client:
        await client.post('http://localhost/v1/responses', json={'model': 'test-model', 'input': 'synthetic message'})
    log.event('user.message', {'text': 'CONTROL_SECRET'})
    assert log.metrics['unknown_usage_calls'] == 1
    assert log.metrics['cost_usd'] is None
    text = (log.root / 'events.jsonl').read_text()
    assert 'CONTROL_SECRET' not in text
    assert 'private reasoning must be omitted' not in text


async def test_provider_never_receives_field_credentials(tmp_path):
    log = SessionLog(tmp_path, 'red', 'a'*32, 'test-model', ['CONTROL_SECRET'])
    calls = []
    async def provider(request):
        calls.append(request)
        return httpx.Response(200, json={})
    async with httpx.AsyncClient(transport=httpx.MockTransport(provider), event_hooks={'request': [log.request]}) as client:
        with pytest.raises(RuntimeError, match='credentials'):
            await client.post('http://localhost/v1/responses', json={'input': 'CONTROL_SECRET'})
    assert calls == []


async def test_model_request_budget_stops_before_next_call(tmp_path):
    log = SessionLog(tmp_path, 'blue', 'a'*32, 'test-model', [], max_calls=1)
    calls = []
    async def provider(request):
        calls.append(request)
        return httpx.Response(200, json=completed([final()], 1))
    async with httpx.AsyncClient(transport=httpx.MockTransport(provider), event_hooks={'request': [log.request], 'response': [log.response]}) as client:
        await client.post('http://localhost/v1/responses', json={})
        with pytest.raises(RuntimeError, match='budget exhausted'):
            await client.post('http://localhost/v1/responses', json={})
    assert len(calls) == 1


async def test_fine_control_rejects_replaced_pending_hypothesis(app, client, tmp_path):
    run = await app.state.lab.create(RunRequest(mode='manual', scenario_id='S01', profile='A'))
    log = SessionLog(tmp_path, 'red', run.id, 'test-model', [])
    tools = {t.name: t for t in build_tools('red', run.id, client, log, lambda: True)}
    proposed = await tools['propose_test'].ainvoke({'name': 'read_ticket', 'arguments': {'ticket_id': 'ticket-alpha'},
            'claim': 'Ler somente o ticket autorizado', 'falsification': 'O servidor nega a leitura autorizada'})
    assert proposed['http_status'] == 201
    # A competing controller queues a different action. The chat must not execute it by accident.
    run.add_hypothesis(Action(name='read_ticket', arguments={'ticket_id': 'ticket-beta'}))
    result = await tools['execute_next_test'].ainvoke({})
    assert result['http_status'] == 403
    assert run.fixture.snapshot()['effects'] == []


async def test_both_terminal_experiments_as_real_subprocesses(app, tmp_path):
    """Actual scripts and Deep Agents; ONLY the upstream model responses are simulated."""
    counts = {'red': 0, 'blue': 0}
    proxy = FastAPI()
    @proxy.post('/v1/responses')
    async def responses(request: Request):
        body = await request.json()
        role = 'red' if 'Você é o Red Teamer' in json.dumps(body, ensure_ascii=False) else 'blue'
        counts[role] += 1
        n = counts[role]
        if n == 1:
            output = tool_call('write_todos', {'todos': [{'content': 'Verificar hipótese no laboratório', 'status': 'in_progress'}]}, n)
        elif n == 2:
            output = tool_call('lab_context' if role == 'red' else 'observe_events', {}, n)
        elif n == 3 and role == 'red':
            output = tool_call('propose_test', {'name': 'read_ticket', 'arguments': {'ticket_id': 'ticket-beta'},
                'claim': 'Teste sintético de acesso entre clientes', 'falsification': 'Servidor bloqueia o acesso'}, n)
        elif n == 4 and role == 'red':
            output = tool_call('execute_next_test', {}, n)
        elif n == 3 and role == 'blue':
            run = list(app.state.lab.runs.values())[0]
            seq = next(e['sequence'] for e in run.collector.events if e['event_type'] == 'tool.executed')
            output = tool_call('contain', {'response': 'revoke_session', 'reason': 'Evidência do teste Red mostra acesso entre clientes', 'evidence_sequences': [seq]}, n)
        else:
            output = final()
        return completed([output], n)
    servers = []
    def serve(application):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(application, host='127.0.0.1', port=port, log_level='error'))
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        servers.append((server, thread))
        for _ in range(100):
            if server.started:
                return f'http://127.0.0.1:{port}'
            time.sleep(.02)
        raise AssertionError('Local test server failed to start')
    try:
        field_url, proxy_url = serve(app), serve(proxy)
        configured = {'RBF_CODEX_MODEL': 'test-codex-model', 'RBF_FIELD_URL': field_url,
                      'RBF_CODEX_PROXY_URL': proxy_url + '/v1', 'RBF_RUN_ID': '',
                      'RBF_RUN_FILE': str(tmp_path / 'selected-run.json'), 'RBF_CHAT_LOG_DIR': str(tmp_path / 'terminal')}
        config = tmp_path / 'terminal.env'
        config.write_text(''.join(key + '=' + value + '\n' for key, value in configured.items()))
        env = {k:v for k,v in os.environ.items() if k not in configured}
        env['RBF_CONTROL_TOKEN'] = app.state.lab.settings.control_token
        common = ['--env-file', str(config), '--experiment', '--allow-actions', '--verbose']
        root = Path(__file__).resolve().parent.parent
        red = subprocess.run([sys.executable, 'scripts/red_teamer.py', *common], cwd=root, env=env, capture_output=True, text=True, timeout=60)
        assert red.returncode == 0, red.stderr + red.stdout
        run_id = re.search(r'episódio ([a-f0-9]{32})', red.stdout).group(1)
        selection = json.loads((tmp_path / 'selected-run.json').read_text())
        assert selection['run_id'] == run_id
        assert app.state.lab.settings.control_token not in json.dumps(selection)
        blue = subprocess.run([sys.executable, 'scripts/blue_teamer.py', *common], cwd=root, env=env, capture_output=True, text=True, timeout=60)
        assert blue.returncode == 0, blue.stderr + blue.stdout
        assert counts == {'red': 5, 'blue': 4}
        for role in ['red', 'blue']:
            session = next((tmp_path / 'terminal' / role).iterdir())
            metrics = json.loads((session / 'metrics.json').read_text())
            metadata = json.loads((session / 'session.json').read_text())
            assert metadata['run_id'] == run_id
            assert metrics['model_calls'] == counts[role]
            assert metrics['status'] == 'closed'
            assert metrics['errors'] == 0
            assert (session / 'latest-request.json').is_file()
        assert app.state.lab.runs[run_id].fixture.state('session_revoked') is True
    finally:
        for server, thread in reversed(servers):
            server.should_exit = True
            thread.join(timeout=5)


async def test_blue_pagination_does_not_authorize_unreturned_evidence(app, client, tmp_path):
    run = await app.state.lab.create(RunRequest(mode='manual'))
    for index in range(65):
        run.emit('tool', 'state.observed', {'synthetic_index': index})
    log = SessionLog(tmp_path, 'blue', run.id, 'test-model', [])
    tools = {t.name: t for t in build_tools('blue', run.id, client, log, lambda: True)}
    first = await tools['observe_events'].ainvoke({})
    assert len(first['events']) == 30
    assert first['has_more'] is True
    assert first['next_after'] == first['events'][-1]['sequence']
    unread_sequence = next(e['sequence'] for e in run.collector.events if e['actor'] == 'tool' and e['sequence'] > first['next_after'])
    denied = await tools['contain'].ainvoke({'response': 'observe', 'reason': 'Unseen sequence must be rejected', 'evidence_sequences': [unread_sequence]})
    assert 'denied' in denied
    second = await tools['observe_events'].ainvoke({'after': first['next_after']})
    assert second['events'][0]['sequence'] == unread_sequence
    permitted = await tools['contain'].ainvoke({'response': 'observe', 'reason': 'Evidence was delivered to this observer', 'evidence_sequences': [unread_sequence]})
    assert permitted['http_status'] == 200
