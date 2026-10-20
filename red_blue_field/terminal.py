"""Two observable Deep Agents chats over the existing native Codex proxy."""
from __future__ import annotations

import argparse
import asyncio
import ipaddress
import json
import os
import re
from importlib.metadata import version
from pathlib import Path
from io import StringIO
from urllib.parse import urlsplit

import httpx
from dotenv import dotenv_values
from deepagents import create_deep_agent, GeneralPurposeSubagentProfile, HarnessProfile, register_harness_profile
from deepagents.backends import StateBackend
from langchain.agents.middleware import AgentMiddleware, TodoListMiddleware
from langchain_core.messages import ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langsmith import tracing_context

from .evidence import atomic_json, digest
from .terminal_logs import SessionLog
from .terminal_tools import build_tools
from .terminal_config import defaults, read_selected_run, save_selected_run

VIRTUAL_TOOLS = {'write_todos', 'ls', 'read_file', 'write_file', 'edit_file', 'glob', 'grep'}


def loopback_url(value: str) -> str:
    endpoint = urlsplit(value)
    try:
        local = endpoint.hostname == 'localhost' or ipaddress.ip_address(endpoint.hostname or '').is_loopback
    except ValueError:
        local = False
    if endpoint.scheme not in {'http', 'https'} or not local or endpoint.username or endpoint.password or endpoint.query or endpoint.fragment:
        raise argparse.ArgumentTypeError('Use a loopback HTTP(S) URL without credentials, query or fragment')
    return value.rstrip('/')


def load_control_token(path: Path) -> str:
    value = os.getenv('RBF_CONTROL_TOKEN', '')
    if not value:
        text = path.read_text().strip()
        # Accept an explicitly selected .env file; do not execute shell or read provider credentials.
        if re.search(r'(?m)^\s*(?:export\s+)?RBF_CONTROL_TOKEN\s*=', text):
            value = dotenv_values(stream=StringIO(text), interpolate=False).get('RBF_CONTROL_TOKEN') or ''
        else:
            value = text
    if len(value) < 24 or '\n' in value:
        raise ValueError('Set RBF_CONTROL_TOKEN or select its token file with --control-token-file')
    return value


class RoleBoundary(AgentMiddleware):
    """Enforce tools independently of editable prompts and upstream harness profiles."""
    def __init__(self, names, log, max_tools=8):
        self.names, self.log, self.max_tools = set(names) | VIRTUAL_TOOLS, log, max_tools
        self.turn_tools = 0

    async def awrap_model_call(self, request, handler):
        tools = [t for t in request.tools if (t.get('name') if isinstance(t, dict) else t.name) in self.names]
        return await handler(request.override(tools=tools))

    async def awrap_tool_call(self, request, handler):
        call = request.tool_call
        self.turn_tools += 1
        self.log.metrics['tool_calls'] += 1
        self.log.event('tool.requested', {'name': call['name'], 'arguments': call['args'], 'tool_call_id': call['id']})
        if call['name'] not in self.names or self.turn_tools > self.max_tools:
            self.log.metrics['tool_denials'] += 1
            self.log.event('tool.denied', {'name': call['name'], 'reason': 'role boundary or turn tool budget'})
            return ToolMessage(content='Denied by the local role/tool budget boundary.', tool_call_id=call['id'])
        result = await handler(request)
        content = result.content if isinstance(result, ToolMessage) else str(result)
        try:
            value = json.loads(content) if isinstance(content, str) else content
        except (ValueError, TypeError):
            value = None
        if isinstance(value, dict) and (value.get('denied') or value.get('http_status', 200) >= 400):
            self.log.metrics['tool_denials'] += 1
        self.log.event('plan.updated' if call['name'] == 'write_todos' else 'tool.responded',
                       {'name': call['name'], 'tool_call_id': call['id'], 'result': content})
        return result


def build_agent(role, model, tools, log, prompt, max_tools=8):
    # Override the library's model-specific Codex persona; retain explicit, logged framework mechanisms.
    register_harness_profile('openai:' + model.model_name, HarnessProfile(base_system_prompt='', system_prompt_suffix='',
        general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False), excluded_tools=frozenset({'execute', 'task', 'delete'})))
    boundary = RoleBoundary([t.name for t in tools], log, max_tools)
    planning = TodoListMiddleware(system_prompt='Use write_todos para registrar e revisar um plano curto, com hipóteses e critérios de verificação.',
        tool_description='Registre tarefas observáveis com estado pending, in_progress ou completed. Revise o plano conforme a evidência.')
    agent = create_deep_agent(model=model, tools=tools, system_prompt=prompt, backend=StateBackend(),
                              middleware=[boundary, planning], checkpointer=InMemorySaver(), name=role + '_teamer')
    return agent, boundary


def arguments(role, argv=None):
    env_file, token_file, configured = defaults(argv)
    parser = argparse.ArgumentParser(description=f'Mini chat {role.upper()} via Deep Agents e proxy local do Codex')
    parser.add_argument('--env-file', type=Path, default=env_file, help='Configuracao literal, sem executar shell ou expandir variaveis')
    parser.add_argument('--proxy-url', type=loopback_url, default=configured('RBF_CODEX_PROXY_URL', 'http://127.0.0.1:8000/v1'))
    parser.add_argument('--model', default=configured('RBF_CODEX_MODEL'), required=not bool(configured('RBF_CODEX_MODEL')),
                        help='Identificador concreto disponível na sua conta; sem aliases ou acesso ampliado')
    parser.add_argument('--field-url', type=loopback_url, default=configured('RBF_FIELD_URL', 'http://127.0.0.1:8080'))
    parser.add_argument('--control-token-file', type=Path, default=token_file)
    parser.add_argument('--run-id', default=configured('RBF_RUN_ID'))
    parser.add_argument('--run-file', type=Path, default=Path(configured('RBF_RUN_FILE', 'artifacts/private/active-run.json')))
    parser.add_argument('--scenario', default='S01', choices=[f'S{i:02}' for i in range(1, 19)])
    parser.add_argument('--profile', default='A', choices=list('ABCD'))
    parser.add_argument('--system-prompt', type=Path, default=Path(__file__).parent / 'prompts' / (role + '_terminal.md'))
    parser.add_argument('--log-dir', type=Path, default=Path(configured('RBF_CHAT_LOG_DIR', 'artifacts/private/chats')))
    parser.add_argument('--max-model-calls', type=int, default=40)
    parser.add_argument('--max-reported-tokens', type=int, default=100000)
    parser.add_argument('--max-tool-calls', type=int, default=8, help='Por turno, incluindo planejamento e arquivos virtuais')
    parser.add_argument('--turn-timeout', type=int, default=120)
    parser.add_argument('--episode-seconds', type=int, default=3600, help='Prazo do episódio novo; o chat jamais renova esse prazo')
    parser.add_argument('--allow-actions', action='store_true', help='Habilitar execução ou contenção nesta sessão')
    parser.add_argument('--experiment', action='store_true', help='Executar o experimento do papel e encerrar o chat')
    parser.add_argument('--verbose', action='store_true', help='Mostrar chamadas, ferramentas e mudanças do plano no terminal')
    parser.add_argument('--prompt', help='Executar uma mensagem e encerrar o chat')
    result = parser.parse_args(argv)
    # argparse does not consistently apply type validators to values supplied through environment defaults.
    result.proxy_url, result.field_url = loopback_url(result.proxy_url), loopback_url(result.field_url)
    for name in ['max_model_calls', 'max_reported_tokens', 'max_tool_calls', 'turn_timeout', 'episode_seconds']:
        if getattr(result, name) < 1:
            parser.error(f'--{name.replace("_", "-")} must be positive')
    if result.episode_seconds > 3600:
        parser.error('--episode-seconds must be at most 3600')
    if role == 'blue' and not result.run_id:
        try:
            result.run_id = read_selected_run(result.run_file, result.field_url)
        except (OSError, ValueError, TypeError) as error:
            parser.error('Blue needs --run-id, RBF_RUN_ID or a valid --run-file: ' + str(error))
    if result.run_id and not re.fullmatch('[a-f0-9]{32}', result.run_id):
        parser.error('Invalid run ID; expected 32 lowercase hexadecimal characters')
    return result


async def chat(role, args):
    token = load_control_token(args.control_token_file)
    prompt = args.system_prompt.read_text()
    log = None
    async with httpx.AsyncClient(base_url=args.field_url, headers={'X-Control-Token': token}, timeout=30, trust_env=False, follow_redirects=False) as field:
        if not args.run_id:
            created = await field.post('/api/runs', json={'scenario_id': args.scenario, 'profile': args.profile, 'mode': 'manual',
                'budget': {'wall_time_seconds': args.episode_seconds}})
            created.raise_for_status()
            args.run_id = created.json()['id']
        context = await field.get('/api/runs/' + args.run_id)
        context.raise_for_status()
        value = context.json()
        if value['request']['mode'] != 'manual':
            raise ValueError('Attach a manual episode to avoid a second automatic planner')
        if value['status'] in {'complete', 'interrupted', 'invalid'}:
            raise ValueError('Episode is closed; create a new manual episode')
        if role == 'red':
            save_selected_run(args.run_file, args.field_url, value)
        log = SessionLog(args.log_dir, role, args.run_id, args.model, [token], max_calls=args.max_model_calls, max_tokens=args.max_reported_tokens)
        log.echo = args.verbose
        enabled = args.allow_actions
        tools = build_tools(role, args.run_id, field, log, lambda: enabled)
        metadata = {'session_id': log.id, 'run_id': args.run_id, 'role': role, 'model': args.model, 'proxy_url': args.proxy_url,
            'protocol': 'responses', 'provider': 'codex_proxy', 'system_prompt': prompt, 'prompt_sha256': digest(prompt),
            'field_episode_mode': 'manual', 'automatic_external_tracing': False, 'host_filesystem': False,
            'tools': [t.name for t in tools], 'max_model_calls': args.max_model_calls, 'max_reported_tokens': args.max_reported_tokens,
            'max_tools_per_turn': args.max_tool_calls, 'dependencies': {p: version(p) for p in ['deepagents', 'langchain-openai', 'langchain-core', 'langgraph']}}
        atomic_json(log.root / 'session.json', log.clean(metadata))
        (log.root / 'session.json').chmod(0o600)
        log.event('session.started', metadata)
        print(f'{role.upper()} · episódio {args.run_id}\nLogs: {log.root}\nAções: {"habilitadas" if enabled else "aguardam /allow"}')
        print(f'RUN_ID={args.run_id}\nArquivo do episodio: {args.run_file}')
        print('Comandos: /help, /allow, /metrics, /reset, /finish, /stop, /quit. Sair preserva o episódio para o outro terminal.')
        try:
            async with httpx.AsyncClient(timeout=args.turn_timeout, trust_env=False, follow_redirects=False,
                    event_hooks={'request': [log.request], 'response': [log.response]}) as provider:
                model = ChatOpenAI(model=args.model, base_url=args.proxy_url, api_key='local-proxy', use_responses_api=True,
                                   store=False, use_previous_response_id=False, max_retries=0, streaming=False,
                                   http_async_client=provider, http_socket_options=(), model_kwargs={'parallel_tool_calls': False})
                agent, boundary = build_agent(role, model, tools, log, prompt, args.max_tool_calls)
                config = {'configurable': {'thread_id': log.id}, 'recursion_limit': 40}
                one_shot = args.prompt
                if args.experiment:
                    path = Path(__file__).resolve().parent.parent / 'experiments' / (role + '_terminal.json')
                    if not path.exists():
                        path = Path(__file__).parent / 'data' / 'experiments' / (role + '_terminal.json')
                    experiment = json.loads(path.read_text())
                    if value['scenario_id'] != experiment['scenario_id']:
                        raise ValueError('Built-in terminal experiments require scenario S01')
                    one_shot = experiment['prompt']
                    log.event('experiment.started', experiment)
                while True:
                    try:
                        message = one_shot if one_shot is not None else await asyncio.to_thread(input, '\nVocê> ')
                    except EOFError:
                        break
                    if message in {'/quit', '/sair'}:
                        break
                    if message == '/help':
                        print('/allow habilita ações somente no próximo turno; /reset limpa a memória do chat, preservando os logs e o alvo.')
                        print('/finish conclui o episódio e gera o dataset; /stop interrompe o episódio. Ambos afetam o outro terminal.')
                        continue
                    if message in {'/finish', '/stop'}:
                        result = await field.post('/api/runs/' + args.run_id + ('/finish' if message == '/finish' else '/stop'))
                        result.raise_for_status()
                        log.event('operator.episode_closed', {'command': message, 'status': result.json()['status']})
                        print('Episódio encerrado. Os artefatos do Field podem ser exportados pelo painel.')
                        break
                    if message == '/allow':
                        enabled = True
                        log.event('operator.actions_enabled', {'duration': 'next_turn'})
                        print('Ações habilitadas para a próxima mensagem.')
                        continue
                    if message == '/metrics':
                        print(json.dumps(log.metrics, ensure_ascii=False, indent=2))
                        continue
                    if message == '/reset':
                        config['configurable']['thread_id'] += '-reset'
                        log.event('memory.reset', {'scope': 'conversation_only'})
                        continue
                    if not message.strip():
                        continue
                    boundary.turn_tools = 0
                    log.metrics['turns'] += 1
                    log.event('user.message', {'text': message, 'actions_enabled': enabled})
                    try:
                        with tracing_context(enabled=False):
                            async with asyncio.timeout(args.turn_timeout):
                                state = await agent.ainvoke({'messages': [{'role': 'user', 'content': message}]}, config=config)
                        answer = state['messages'][-1].text
                        print(f'\n{role.upper()}> {answer}')
                        log.event('assistant.message', {'text': answer, 'todos': state.get('todos', [])})
                        print(f"[sessão] {log.metrics['model_calls']} chamadas; {log.metrics['input_tokens']} tokens de entrada; {log.metrics['output_tokens']} de saída.")
                    except Exception as error:
                        log.metrics['errors'] += 1
                        log.event('turn.failed', {'error_type': type(error).__name__, 'message': str(error)})
                        print(f'Turno interrompido: {type(error).__name__}. Consulte os logs; /reset permite recomeçar a conversa.')
                        if one_shot is not None:
                            raise RuntimeError('Experiment failed; see the session logs') from None
                    finally:
                        enabled = args.allow_actions
                    if one_shot is not None:
                        break
        except BaseException:
            log.close('interrupted')
            raise
        else:
            log.close()


def main(role):
    try:
        asyncio.run(chat(role, arguments(role)))
    except KeyboardInterrupt:
        print('\nChat interrompido. O episódio conserva seu prazo original.')
    except (OSError, ValueError, RuntimeError, httpx.HTTPError) as error:
        print(f'Falha: {error}')
        raise SystemExit(1) from None
