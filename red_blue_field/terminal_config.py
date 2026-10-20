"""Literal dotenv configuration and a credential-free pointer to the selected run."""
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

from dotenv import dotenv_values

from .evidence import atomic_json, now


def defaults(argv=None):
    preliminary = argparse.ArgumentParser(add_help=False)
    preliminary.add_argument('--env-file', type=Path, default=Path('.env'))
    options, _ = preliminary.parse_known_args(argv)
    if options.env_file.exists():
        values = dotenv_values(options.env_file, interpolate=False)
    elif str(options.env_file) != '.env':
        preliminary.error('Selected --env-file does not exist')
    else:
        values = {}

    def get(key, fallback=None):
        return os.environ.get(key, values.get(key)) or fallback

    token_file = options.env_file if values.get('RBF_CONTROL_TOKEN') else Path('artifacts/private/control-token')
    return options.env_file, token_file, get


def read_selected_run(path: Path, field_url: str) -> str:
    import json
    value = json.loads(path.read_text())
    if not isinstance(value, dict) or value.get('version') != 1 or not isinstance(value.get('run_id'), str) or not re.fullmatch(r'[a-f0-9]{32}', value['run_id']):
        raise ValueError('Selected run file has an invalid format')
    if value.get('field_url') != field_url:
        raise ValueError('Selected run belongs to another Field URL; choose --run-id explicitly')
    return value['run_id']


def save_selected_run(path: Path, field_url: str, run: dict):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    atomic_json(path, {'version': 1, 'run_id': run['id'], 'field_url': field_url,
                       'scenario_id': run['scenario_id'], 'profile': run['profile'],
                       'selected_at': now(), 'status_at_selection': run['status']})
    path.chmod(0o600)
