import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from red_blue_field.evidence import verify_export
from red_blue_field.fielddesk import Denied
from red_blue_field.models import Action, Budget, RunRequest


async def test_control_and_target_identities_are_separate(client, app):
    response = await client.post('/api/runs', json={'scenario_id': 'S01', 'mode': 'manual', 'profile': 'A'})
    assert response.status_code == 201, response.text
    rid = response.json()['id']
    creds = (await client.get(f'/api/runs/{rid}/credentials')).json()
    assert (await client.get('/api/runs', headers={'X-Control-Token': ''})).status_code == 401
    assert (await client.get(f'/lab/{rid}/tickets/ticket-beta')).status_code == 401
    headers = {'Authorization': 'Bearer ' + creds['participant_token']}
    result = await client.get(f'/lab/{rid}/tickets/ticket-beta', headers=headers)
    assert result.status_code == 200
    assert 'RBF_SYNTHETIC_' in result.text
    assert (await client.get('/api/runs', headers={**headers, 'X-Control-Token': ''})).status_code == 401
    other = (await client.post('/api/runs', json={'scenario_id': 'S01'})).json()['id']
    assert (await client.get(f'/lab/{other}/tickets/ticket-alpha', headers=headers)).status_code == 401
    assert (await client.post(f'/lab/{rid}/cloud', headers=headers, json={'operation': 'grant_private'})).status_code == 403
    assert (await client.get('/api/runs', headers={'Origin': 'http://evil.invalid'})).status_code == 403


async def test_manual_http_shares_global_budget(client, app):
    run = await app.state.lab.create(RunRequest(scenario_id='S01', mode='manual', budget=Budget(max_steps=1)))
    headers = {'Authorization': 'Bearer ' + run.tokens['red']}
    assert (await client.get(f'/lab/{run.id}/tickets/ticket-alpha', headers=headers)).status_code == 200
    assert (await client.get(f'/lab/{run.id}/tickets/ticket-alpha', headers=headers)).status_code == 409
    assert run.limits.tool_calls == 1


async def test_review_is_bound_and_denial_blocks_effect(app, client):
    lab = app.state.lab
    run = await lab.create(RunRequest(scenario_id='S06', profile='D'))
    # Model the vulnerable application beneath an independent human intervention gate.
    run.fixture.profile = 'A'
    from red_blue_field.agents import injection
    run.request.mode = 'manual'
    run.add_hypothesis(Action(name='target_task', arguments={'instruction': injection('delete_ticket')}))
    # Profile D's scripted target remains protected. Exercise the independent operation gate directly.
    from red_blue_field.security import NeedsReview
    with pytest.raises(NeedsReview):
        run.reviews.gate({'name': 'target_operation', 'operation': 'delete_ticket'})
    review = lab.store.list('reviews', run.id)[0]
    path = f'/api/runs/{run.id}/reviews/{review["id"]}'
    bad = await client.post(path, json={'decision': 'approve', 'operation_hash': '0' * 64, 'reason': 'Wrong operation'})
    assert bad.status_code == 403
    good = await client.post(path, json={'decision': 'deny', 'operation_hash': review['operation_hash'], 'reason': 'No authorization for deleting the ticket'})
    assert good.status_code == 200
    with pytest.raises(Denied):
        run.reviews.gate({'name': 'target_operation', 'operation': 'delete_ticket'})
    assert len(run.fixture.snapshot()['tickets']) == 2


async def test_refund_approval_is_atomic_under_concurrency(app):
    run = await app.state.lab.create(RunRequest(scenario_id='S04', profile='B'))
    operation = {'name': 'refund', 'amount': 10, 'recipient': 'tenant-a'}
    token = run.fixture.grant_refund(operation)
    def apply(i):
        try:
            return run.fixture.refund(f'key-{i}', 10, 'tenant-a', token)
        except Denied:
            return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(apply, range(8)))
    assert sum(x is not None for x in results) == 1
    assert len(run.fixture.snapshot()['refunds']) == 1
    expired = run.fixture.grant_refund(operation, lifetime=-1)
    with pytest.raises(Denied):
        run.fixture.refund('expired', 10, 'tenant-a', expired)
    mismatched = run.fixture.grant_refund(operation)
    with pytest.raises(Denied):
        run.fixture.refund('wrong', 11, 'tenant-a', mismatched)


async def test_dfs_backtracking_deduplication_and_frontier(app):
    run = await app.state.lab.create(RunRequest(scenario_id='S01', mode='manual', max_depth=1, max_children=1))
    a = Action(name='inventory')
    root = run.add_hypothesis(a)
    duplicate = run.add_hypothesis(a)
    assert duplicate['status'] == 'pruned'
    child = run.add_hypothesis(Action(name='read_ticket', arguments={'ticket_id': 'ticket-alpha'}), root)
    assert child['depth'] == 1
    assert run.add_hypothesis(Action(name='inventory'), child) is None
    assert run.add_hypothesis(Action(name='read_ticket', arguments={'ticket_id': 'ticket-beta'}), root) is None
    await app.state.lab.step(run)
    assert run.history[-1]['action']['name'] == 'read_ticket'
    await app.state.lab.step(run)
    assert run.history[-1]['action']['name'] == 'inventory'
    assert len(run.frontier) == 2


async def test_export_rejects_tampering(app, client):
    run = await app.state.lab.create(RunRequest())
    await app.state.lab.drive(run)
    assert (await client.get(f'/api/runs/{run.id}/export')).status_code == 200
    run.collector.path('state-after.json').write_text('{}')
    with pytest.raises(ValueError, match='hash mismatch'):
        verify_export(run.collector.root)
    assert (await client.get(f'/api/runs/{run.id}/artifacts/control-token')).status_code == 404


async def test_assessment_requires_finished_episode_and_evidence(app, client):
    run = await app.state.lab.create(RunRequest())
    body = {'competency': 'Authorization', 'level': 'guided', 'evidence_refs': ['events.jsonl'], 'explanation': 'The server enforces object ownership.'}
    assert (await client.post(f'/api/runs/{run.id}/assessments', json=body)).status_code == 409
    await app.state.lab.drive(run)
    body['evidence_refs'] = ['invented.json']
    assert (await client.post(f'/api/runs/{run.id}/assessments', json=body)).status_code == 422
    body['evidence_refs'] = ['state-after.json']
    assert (await client.post(f'/api/runs/{run.id}/assessments', json=body)).status_code == 200
    assert verify_export(run.collector.root)['valid']
