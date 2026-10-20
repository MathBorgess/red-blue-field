from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
from pathlib import Path

from .api import create_app
from .config import Settings
from .evidence import verify_export
from .models import RunRequest


def main():
    parser = argparse.ArgumentParser(prog='rbf', description='Bounded red/blue reference laboratory')
    sub = parser.add_subparsers(dest='command', required=True)
    serve = sub.add_parser('serve')
    serve.add_argument('--host', default='127.0.0.1')
    serve.add_argument('--port', type=int, default=8080)
    init = sub.add_parser('init')
    init.add_argument('--output', type=Path, default=Path('.env'))
    demo = sub.add_parser('demo')
    demo.add_argument('--scenario', default='S01')
    demo.add_argument('--profile', choices=list('ABCD'), default='A')
    demo.add_argument('--benign', action='store_true')
    verify = sub.add_parser('verify')
    verify.add_argument('directory', type=Path)
    sub.add_parser('doctor')
    args = parser.parse_args()
    if args.command == 'init':
        data = '\n'.join(f'{key}={secrets.token_urlsafe(32)}' for key in ['RBF_CONTROL_TOKEN', 'RBF_WORKER_A_TOKEN', 'RBF_WORKER_B_TOKEN']) + '\n'
        descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w') as handle:
            handle.write(data)
        print(f'Created {args.output}; existing secrets are never overwritten.')
    elif args.command == 'verify':
        print(json.dumps(verify_export(args.directory), indent=2))
    elif args.command == 'serve':
        import uvicorn
        app = create_app()
        print(f'Control token file: {app.state.lab.settings.data_dir / "control-token"}')
        uvicorn.run(app, host=args.host, port=args.port, access_log=False)
    elif args.command == 'doctor':
        settings = Settings()
        settings.prepare()
        print(json.dumps({'data_directory': str(settings.data_dir), 'control_token_file': str(settings.data_dir / 'control-token'), 'worker_urls_configured': bool(settings.worker_a_url and settings.worker_b_url), 'model_configured': bool(settings.model_url and settings.model_name), 'mcp_red': 'excluded', 'mcp_blue': 'excluded'}, indent=2))
    else:
        async def execute():
            app = create_app()
            lab = app.state.lab
            try:
                run = await lab.create(RunRequest(scenario_id=args.scenario, profile=args.profile, benign=args.benign, mode='scripted', reviewer='scripted_reviewer'))
                await lab.drive(run)
                print(json.dumps({'run': run.public(), 'export': str(run.collector.root), 'verification': verify_export(run.collector.root)}, indent=2, ensure_ascii=False))
            finally:
                await lab.close()
        asyncio.run(execute())


if __name__ == '__main__':
    main()
