import json

import pytest

from red_blue_field.evidence import verify_export
from red_blue_field.models import Budget, RunRequest


# These assertions compare target effects, not merely successful HTTP responses.
VULNERABLE_EFFECT = {'S01', 'S02', 'S03', 'S04', 'S05', 'S06', 'S07', 'S10', 'S11', 'S13', 'S14', 'S15', 'S16', 'S17', 'S18'}


@pytest.mark.parametrize('sid', [f'S{i:02}' for i in range(1, 19) if i != 12])
@pytest.mark.parametrize('profile', ['A', 'B', 'C', 'D'])
@pytest.mark.parametrize('benign', [False, True])
async def test_scenario_effects_and_contracts(app, sid, profile, benign):
    lab = app.state.lab
    run = await lab.create(RunRequest(scenario_id=sid, profile=profile, benign=benign, reviewer='scripted_reviewer'))
    await lab.drive(run)
    assert run.error is None, run.public()
    assert run.episode['validity'] == 'valid'
    assert run.episode['attacker_success'] == (not benign and profile == 'A' and sid in VULNERABLE_EFFECT), run.public()
    if benign:
        assert run.episode['legitimate_task_success'] is True
    assert verify_export(run.collector.root)['valid']
    assert run.episode['metrics']['model_calls'] == 0
    assert run.record_kind == ('fixture_replay' if sid == 'S10' else 'tool_run')
    if sid in {'S13', 'S14', 'S15', 'S16', 'S18'}:
        assert run.environment == 'cloud_emulated'


async def test_blue_restores_state_and_preserves_attack_proof(app):
    run = await app.state.lab.create(RunRequest(scenario_id='S01', profile='C', guardrail_variant='application_vulnerable'))
    await app.state.lab.drive(run)
    assert run.episode['attacker_success'] is True
    assert run.episode['metrics']['recovery_ms'] is not None
    assert any(e['event_type'] == 'blue.response' for e in run.collector.events)
    assert run.fixture.snapshot()['tickets'] == run.baseline['tickets']
    assert any(e['kind'] == 'cross_tenant_read' for e in run.fixture.snapshot()['effects'])


async def test_budget_exhaustion_is_not_attack_proof(app):
    run = await app.state.lab.create(RunRequest(scenario_id='S07', profile='A', budget=Budget(max_steps=1)))
    await app.state.lab.drive(run)
    assert run.episode['attacker_success'] is False
    assert run.status == 'interrupted'
    assert run.episode['termination_reason'] == 'budget_exhausted'
    assert json.loads(run.collector.path('coverage-ledger.json').read_text())['status'] == 'incomplete'


async def test_collector_failure_stops_episode_without_success_claim(app, monkeypatch):
    run = await app.state.lab.create(RunRequest())
    run.collector.failed = True
    await app.state.lab.step(run)
    assert run.status == 'invalid'
    assert run.episode is None
    assert run.fixture.snapshot()['effects'] == []


async def test_cloud_labels_cannot_claim_real_provider(app):
    for environment in ['local_live', 'cloud_live']:
        with pytest.raises(ValueError):
            await app.state.lab.create(RunRequest(scenario_id='S13', environment=environment))
