import asyncio
import json

import httpx
import pytest

from red_blue_field.api import create_app
from red_blue_field.config import Settings
from red_blue_field.evidence import verify_export
from red_blue_field.models import Budget, CampaignRequest, RunRequest


def provider(app, handler):
    lab = app.state.lab
    lab.settings.model_url = 'https://provider.invalid/v1'
    lab.settings.model_name = 'test-model'
    lab.settings.model_key = 'provider-secret-never-export'
    lab.settings.model_input_usd_per_million = 0
    lab.settings.model_output_usd_per_million = 0
    lab.broker.transport = httpx.MockTransport(handler)


async def test_real_broker_protocol_with_mock_provider(app):
    calls = []
    def handler(request):
        calls.append(json.loads(request.content))
        assert request.headers['Authorization'] == 'Bearer provider-secret-never-export'
        answer = {'action': {'name': 'read_ticket', 'arguments': {'ticket_id': 'ticket-beta'}, 'reason': 'Test ownership'}, 'claim': 'Ownership may not be enforced', 'falsification': 'The server denies the cross-tenant read'} if len(calls) == 1 else {'stop': True}
        return httpx.Response(200, json={'choices': [{'message': {'content': json.dumps(answer)}}], 'usage': {'prompt_tokens': 50, 'completion_tokens': 30, 'total_tokens': 80}})
    provider(app, handler)
    run = await app.state.lab.create(RunRequest(scenario_id='S01', profile='A', mode='bounded_autonomous'))
    await app.state.lab.drive(run)
    assert run.error is None, run.public()
    assert run.episode['attacker_success'] is True
    assert run.episode['metrics']['model_calls'] == 2
    assert run.episode['metrics']['total_tokens'] == 160
    assert run.record_kind == 'model_run'
    assert verify_export(run.collector.root)['valid']
    assert all('provider-secret-never-export' not in p.read_text() for p in run.collector.root.iterdir() if p.is_file())


async def test_provider_failure_charges_reserved_budget_without_claiming_effect(app):
    provider(app, lambda request: httpx.Response(429, json={'error': 'test rate limit'}))
    run = await app.state.lab.create(RunRequest(mode='bounded_autonomous'))
    await app.state.lab.drive(run)
    assert run.status == 'invalid'
    assert run.episode['attacker_success'] is None
    assert run.limits.total_tokens > 0
    assert any('Actual usage is unknown' in item for item in run.limitations)


async def test_zero_model_budget_prevents_network_call(app):
    calls = []
    provider(app, lambda request: calls.append(request))
    run = await app.state.lab.create(RunRequest(mode='bounded_autonomous', budget=Budget(max_model_calls=0)))
    await app.state.lab.drive(run)
    assert calls == []
    assert run.limits.model_calls == 0
    assert run.episode['termination_reason'] == 'budget_exhausted'


async def test_finished_archive_can_be_inspected_after_restart(tmp_path):
    settings = Settings(data_dir=tmp_path, control_token='test-control-token-' + 'x' * 24)
    first = create_app(settings)
    run = await first.state.lab.create(RunRequest())
    await first.state.lab.drive(run)
    await first.state.lab.close()
    second = create_app(settings)
    try:
        assert run.id in second.state.lab.runs
        archived = second.state.lab.runs[run.id]
        assert archived.status == 'complete'
        assert archived.tokens == {}
        assert verify_export(archived.collector.root)['valid']
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=second), base_url='http://test', headers={'X-Control-Token': settings.control_token}) as client:
            assert (await client.get(f'/api/runs/{run.id}/export')).status_code == 200
            assert (await client.get(f'/api/runs/{run.id}/credentials')).status_code == 409
    finally:
        await second.state.lab.close()


async def test_restart_does_not_resume_pending_episode(tmp_path):
    settings = Settings(data_dir=tmp_path, control_token='test-control-token-' + 'x' * 24)
    first = create_app(settings)
    run = await first.state.lab.create(RunRequest(mode='manual'))
    run.watchdog.cancel()
    # Simulate a crashed process, without its graceful shutdown handler.
    second = create_app(settings)
    try:
        archived = second.state.lab.runs[run.id]
        assert archived.status == 'interrupted'
        assert archived.tokens == {}
        assert archived.episode is None
        assert 'reconciliation' in archived.error
    finally:
        await second.state.lab.close()
        await first.state.lab.close()


async def test_campaign_cancel_preserves_stopped_status(app):
    lab = app.state.lab
    campaign = await lab.campaign(CampaignRequest(scenarios=['S01'], profiles=['A'], repetitions=3))
    task = lab.campaign_tasks[campaign['id']]
    await asyncio.sleep(0)
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    assert lab.store.get('campaigns', campaign['id'])['status'] == 'stopped'
    for run in lab.runs.values():
        assert run.status in {'complete', 'interrupted', 'invalid'}
