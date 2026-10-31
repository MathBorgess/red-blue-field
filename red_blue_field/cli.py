from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
from pathlib import Path

from .api import create_app
from .config import Settings, resources
from .evidence import verify_export
from .mcp import MCPServer, run_stdio_loop
from .models import RunRequest
from .signing import generate_keypair, sign_export, verify_signature


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
    verify.add_argument('--public-key', default=None)
    verify.add_argument('--require-signature', action='store_true')
    keygen = sub.add_parser('keygen')
    keygen.add_argument('--private', type=Path, required=True)
    keygen.add_argument('--public', type=Path, required=True)
    keygen.add_argument('--signer', default='human:auditor')
    sign = sub.add_parser('sign')
    sign.add_argument('directory', type=Path)
    sign.add_argument('--private', type=Path, required=True)
    sign.add_argument('--signer', default='human:auditor')
    mcp = sub.add_parser('mcp')
    mcp.add_argument('--role', choices=['red', 'blue'], required=True)
    sub.add_parser('doctor')
    args = parser.parse_args()
    if args.command == 'init':
        template = resources() / '.env.example'
        if not template.exists():
            template = resources() / 'env.example'
        tokens = {key: secrets.token_urlsafe(32) for key in ['RBF_CONTROL_TOKEN', 'RBF_WORKER_A_TOKEN', 'RBF_WORKER_B_TOKEN']}
        data = '\n'.join(line.split('=', 1)[0] + '=' + tokens[line.split('=', 1)[0]]
                         if line.split('=', 1)[0] in tokens else line for line in template.read_text().splitlines()) + '\n'
        descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w') as handle:
            handle.write(data)
        print(f'Created {args.output}; existing secrets are never overwritten.')
    elif args.command == 'keygen':
        print(json.dumps(generate_keypair(args.private, args.public, args.signer), indent=2))
    elif args.command == 'sign':
        priv_hex = args.private.read_text().strip()
        print(json.dumps(sign_export(args.directory, priv_hex, args.signer), indent=2))
    elif args.command == 'verify':
        if args.require_signature or args.public_key or (args.directory / 'signature.json').is_file():
            print(json.dumps(verify_signature(args.directory, public_key_hex=args.public_key), indent=2))
        else:
            print(json.dumps(verify_export(args.directory), indent=2))
    elif args.command == 'mcp':
        settings = Settings()
        app = create_app(settings)
        server = MCPServer(app.state.lab, args.role)
        asyncio.run(run_stdio_loop(server, token=settings.control_token))
    elif args.command == 'serve':
        import uvicorn
        app = create_app()
        print(f'Control token file: {app.state.lab.settings.data_dir / "control-token"}')
        uvicorn.run(app, host=args.host, port=args.port, access_log=False)
    elif args.command == 'doctor':
        settings = Settings()
        settings.prepare()
        print(json.dumps({'data_directory': str(settings.data_dir), 'control_token_file': str(settings.data_dir / 'control-token'), 'worker_urls_configured': bool(settings.worker_a_url and settings.worker_b_url), 'model_configured': False, 'mcp_red': 'ready', 'mcp_blue': 'ready'}, indent=2))
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
