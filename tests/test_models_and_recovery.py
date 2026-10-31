import asyncio
import json

import httpx
import pytest

from red_blue_field.api import create_app
from red_blue_field.config import Settings
from red_blue_field.evidence import verify_export
from red_blue_field.models import Budget, CampaignRequest, RunRequest


async def test_legacy_model_modes_cannot_start_new_runs_or_campaigns(app, client):
    for mode in ('agent_assisted', 'bounded_autonomous'):
        result = await client.post('/api/runs', json={'mode': mode})
        assert result.status_code == 422
        result = await client.post('/api/campaigns', json={'mode': mode})
        assert result.status_code == 422
    assert not app.state.lab.runs


async def test_signed_legacy_model_archive_survives_restart_read_only(tmp_path, monkeypatch):
    import hashlib
    import zipfile
    from pathlib import Path
    from red_blue_field.signing import verify_signature

    fixture = Path(__file__).parent / 'fixtures' / 'legacy-model-run.zip'
    with zipfile.ZipFile(fixture) as source:
        source.extractall(tmp_path)
    run_dir = next((tmp_path / 'runs').iterdir())
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in run_dir.iterdir() if p.is_file()}
    settings = Settings(data_dir=tmp_path, control_token='test-control-token-' + 'x' * 24)
    app = create_app(settings)
    try:
        run = app.state.lab.runs[run_dir.name]
        assert run.status == 'complete'
        assert run.record_kind == 'model_run'
        assert run.request.mode == 'bounded_autonomous'
        assert run.tokens == {}
        async def unexpected_cancel():
            raise AssertionError('a finished archive must not cancel a worker')
        monkeypatch.setattr(run.tools, 'cancel_worker', unexpected_cancel)
        assert verify_signature(run_dir)['signed']
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test', headers={'X-Control-Token': settings.control_token}) as client:
            assert (await client.get(f'/api/runs/{run.id}')).status_code == 200
            assert (await client.get(f'/api/runs/{run.id}/artifacts')).status_code == 200
            assert (await client.get(f'/api/runs/{run.id}/export')).status_code == 200
            assert (await client.get(f'/api/runs/{run.id}/credentials')).status_code == 409
            assert (await client.post(f'/api/runs/{run.id}/stop')).status_code == 200
            result = await client.post(f'/api/runs/{run.id}/assessments', json={'competency':'legacy', 'level':'not_assessed', 'explanation':'historical archive'})
            assert result.status_code == 409
            result = await client.post(f'/api/runs/{run.id}/findings', json={'status':'rejected', 'reason':'historical archive'})
            assert result.status_code == 409
            result = await client.post(f'/api/runs/{run.id}/sign', json={'signer_id':'human:reviewer', 'private_key_hex':'0'*64})
            assert result.status_code == 409
        assert {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in run_dir.iterdir() if p.is_file()} == before
        assert app.state.lab.store.get('runs', run.id)['status'] == 'complete'
        assert verify_signature(run_dir)['signed']
    finally:
        await app.state.lab.close()


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
            assert (await client.post(f'/api/runs/{run.id}/stop')).status_code == 200
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
