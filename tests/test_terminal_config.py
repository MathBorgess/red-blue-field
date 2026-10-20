import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip('dotenv')
pytest.importorskip('deepagents')
from dotenv import dotenv_values

from red_blue_field.terminal import arguments, load_control_token
from red_blue_field.terminal_config import read_selected_run, save_selected_run


@pytest.fixture(autouse=True)
def isolated_client_environment(monkeypatch):
    for name in ['RBF_CODEX_MODEL', 'RBF_FIELD_URL', 'RBF_RUN_ID', 'RBF_CODEX_PROXY_URL', 'RBF_RUN_FILE', 'RBF_CHAT_LOG_DIR', 'RBF_CONTROL_TOKEN']:
        monkeypatch.delenv(name, raising=False)


def test_init_generates_complete_configuration_without_overwriting(tmp_path):
    path = tmp_path / '.env'
    first = subprocess.run([sys.executable, '-m', 'red_blue_field.cli', 'init', '--output', str(path)], capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    config = dotenv_values(path, interpolate=False)
    secrets = [config[k] for k in ['RBF_CONTROL_TOKEN', 'RBF_WORKER_A_TOKEN', 'RBF_WORKER_B_TOKEN']]
    assert len(set(secrets)) == 3 and all(len(s) >= 24 for s in secrets)
    assert config['RBF_CODEX_MODEL'] == ''
    assert config['RBF_RUN_ID'] == ''
    assert config['RBF_RUN_FILE'] == 'artifacts/private/active-run.json'
    assert path.stat().st_mode & 0o777 == 0o600
    assert all(secret not in first.stdout + first.stderr for secret in secrets)
    before = path.read_bytes()
    second = subprocess.run([sys.executable, '-m', 'red_blue_field.cli', 'init', '--output', str(path)], capture_output=True, text=True)
    assert second.returncode != 0
    assert path.read_bytes() == before


def test_dotenv_defaults_are_literal_and_flags_override_environment(tmp_path, monkeypatch):
    for name in ['RBF_CODEX_MODEL', 'RBF_FIELD_URL', 'RBF_RUN_ID', 'RBF_CODEX_PROXY_URL', 'RBF_RUN_FILE']:
        monkeypatch.delenv(name, raising=False)
    config = tmp_path / 'client.env'
    config.write_text('RBF_CODEX_MODEL="file-model"\nRBF_FIELD_URL=http://localhost:9080\nRBF_RUN_ID=\nRBF_CODEX_PROXY_URL=http://localhost:9000/v1\n')
    value = arguments('red', ['--env-file', str(config)])
    assert value.model == 'file-model'
    assert value.field_url == 'http://localhost:9080'
    monkeypatch.setenv('RBF_CODEX_MODEL', 'environment-model')
    assert arguments('red', ['--env-file', str(config)]).model == 'environment-model'
    assert arguments('red', ['--env-file', str(config), '--model', 'flag-model']).model == 'flag-model'
    config.write_text('RBF_CODEX_MODEL=${RBF_OTHER_MODEL}\n')
    monkeypatch.delenv('RBF_CODEX_MODEL')
    monkeypatch.setenv('RBF_OTHER_MODEL', 'must-not-expand')
    assert arguments('red', ['--env-file', str(config)]).model == '${RBF_OTHER_MODEL}'


def test_selected_run_has_no_credentials_and_blue_checks_server(tmp_path, monkeypatch):
    monkeypatch.delenv('RBF_RUN_ID', raising=False)
    pointer = tmp_path / 'selected-run.json'
    run = {'id': 'a'*32, 'scenario_id': 'S01', 'profile': 'A', 'status': 'prepared', 'secret': 'never write extra fields'}
    save_selected_run(pointer, 'http://localhost:9080', run)
    assert read_selected_run(pointer, 'http://localhost:9080') == run['id']
    assert 'secret' not in pointer.read_text()
    assert pointer.stat().st_mode & 0o777 == 0o600
    config = tmp_path / 'client.env'
    config.write_text('RBF_CODEX_MODEL=test-model\nRBF_FIELD_URL=http://localhost:9080\nRBF_RUN_FILE=' + str(pointer) + '\n')
    blue = arguments('blue', ['--env-file', str(config)])
    assert blue.run_id == run['id']
    with pytest.raises(ValueError, match='another Field URL'):
        read_selected_run(pointer, 'http://localhost:8080')
    # Explicit selection wins over the discovery file, including when the file is stale.
    pointer.unlink()
    assert arguments('blue', ['--env-file', str(config), '--run-id', 'b'*32]).run_id == 'b'*32


@pytest.mark.parametrize('record', [[], {}, {'version': 1, 'run_id': 123}, {'version': 1, 'run_id': 'expired-example'}])
def test_invalid_run_file_is_rejected(tmp_path, record):
    path = tmp_path / 'bad.json'
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        read_selected_run(path, 'http://localhost:8080')


def test_token_file_parses_dotenv_without_executing_it(tmp_path, monkeypatch):
    monkeypatch.delenv('RBF_CONTROL_TOKEN', raising=False)
    token = 'synthetic-control-' + 'x'*30
    path = tmp_path / 'token.env'
    path.write_text('export RBF_CONTROL_TOKEN = "' + token + '" # comment\nUNRELATED=$(exit 99)\n')
    assert load_control_token(path) == token
