"""Opt-in integration tests create only isolated, disposable containers."""
import json
import asyncio
import os
import secrets
import subprocess
import time
import urllib.request

import httpx
import pytest

from red_blue_field.models import RunRequest

pytestmark = pytest.mark.skipif(os.getenv('RBF_TEST_DOCKER') != '1', reason='Set RBF_TEST_DOCKER=1 after building the worker image')


@pytest.fixture(scope='module')
def workers():
    env = {k: v for k, v in os.environ.items() if k not in {'DOCKER_HOST', 'DOCKER_CONTEXT', 'DOCKER_TLS', 'DOCKER_TLS_VERIFY', 'DOCKER_CERT_PATH'}}
    def docker(*args):
        return subprocess.check_output(['docker', '--host=unix:///var/run/docker.sock', *args], env=env, text=True).strip()
    network = 'rbf-test-' + secrets.token_hex(5)
    docker('network', 'create', '--internal', network)
    containers = []
    value = {}
    try:
        for profile in ['A', 'B']:
            token = secrets.token_urlsafe(32)
            cid = docker('run', '-d', '--network', network, '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges', '--pids-limit=64', '--memory=384m', '--cpus=0.5', '--tmpfs', '/tmp:size=128m,mode=1777', '--tmpfs', '/proof:size=8m,uid=10001,gid=10001,mode=0700', '-e', 'RBF_WORKER_PROFILE=' + profile, '-e', 'RBF_WORKER_TOKEN=' + token, 'red-blue-field-worker:0.4.0')
            containers.append(cid)
            inspection = json.loads(docker('inspect', cid))[0]
            assert inspection['HostConfig']['ReadonlyRootfs'] is True
            assert inspection['Config']['User'] == '10001:10001'
            assert not inspection['Mounts']
            address = inspection['NetworkSettings']['Networks'][network]['IPAddress']
            url = f'http://{address}:8080'
            with httpx.Client(trust_env=False) as client:
                for _ in range(40):
                    try:
                        if client.get(url + '/health', timeout=1).status_code == 200:
                            break
                    except httpx.HTTPError:
                        time.sleep(0.1)
                else:
                    raise AssertionError('Worker did not start')
            value[profile] = {'url': url, 'token': token, 'cid': cid}
        yield value
    finally:
        for cid in containers:
            docker('rm', '-f', cid)
        docker('network', 'rm', network)


@pytest.mark.parametrize('profile', ['A', 'B', 'C', 'D'])
@pytest.mark.parametrize('benign', [False, True])
async def test_real_marker_execution_isolated(app, workers, profile, benign):
    lab = app.state.lab
    for name, info in workers.items():
        setattr(lab.settings, 'worker_' + name.lower() + '_url', info['url'])
        setattr(lab.settings, 'worker_' + name.lower() + '_token', info['token'])
    run = await lab.create(RunRequest(scenario_id='S12', profile=profile, benign=benign, reviewer='scripted_reviewer'))
    await lab.drive(run)
    assert run.error is None, run.public()
    assert run.episode['attacker_success'] == (profile == 'A' and not benign)
    assert run.episode['validity'] == 'valid'
    from red_blue_field.evidence import verify_export
    assert verify_export(run.collector.root)['valid']


async def test_real_pentagi_tool_profiles(workers):
    info = workers['A']
    async with httpx.AsyncClient(base_url=info['url'], headers={'Authorization': 'Bearer ' + info['token']}, trust_env=False, timeout=90) as client:
        inventory = (await client.get('/tools')).json()['profiles']
        assert inventory['nmap_local']['available']
        assert inventory['sqlmap_fixture']['available']
        assert not inventory['metasploit_version']['available']
        for name in ['http_headers', 'nmap_local', 'sqlmap_fixture', 'filesystem', 'system', 'crypto', 'python', 'network']:
            result = (await client.post('/tools/run', json={'profile': name})).json()
            assert result['status'] == 'executed', (name, result)
            assert result['exit_code'] == 0, (name, result)
            if name == 'nmap_local':
                assert '8080/tcp open' in result['stdout']
            if name == 'sqlmap_fixture':
                assert 'injectable' in result['stdout'] or 'is vulnerable' in result['stdout'], result['stdout']
        assert (await client.post('/tools/run', json={'profile': 'nmap_local', 'target': 'example.com'})).status_code == 422
        assert (await client.post('/tools/run', json={'profile': 'shell'})).status_code == 422


async def test_worker_command_can_be_cancelled_by_episode(workers):
    info = workers['A']
    episode = secrets.token_hex(16)
    async with httpx.AsyncClient(base_url=info['url'], headers={'Authorization': 'Bearer ' + info['token']}, trust_env=False, timeout=90) as client:
        task = asyncio.create_task(client.post('/tools/run', json={'profile': 'nmap_local', 'episode_id': episode}))
        cancelled = False
        for _ in range(20):
            await asyncio.sleep(.03)
            value = (await client.post('/cancel/' + episode, json={})).json()
            if value['cancelled']:
                cancelled = True
                break
        assert cancelled
        result = (await task).json()
        assert result['exit_code'] < 0
        assert (await client.post('/cancel/' + episode, json={})).json()['cancelled'] is False


async def test_blue_does_not_claim_worker_reset_from_database_restore(app, workers):
    lab = app.state.lab
    lab.settings.worker_a_url = workers['A']['url']
    lab.settings.worker_a_token = workers['A']['token']
    run = await lab.create(RunRequest(scenario_id='S12', profile='C', guardrail_variant='application_vulnerable'))
    await lab.drive(run)
    assert run.episode['attacker_success'] is True
    assert run.episode['effect_assessment']['recovery_status'] == 'partial'
