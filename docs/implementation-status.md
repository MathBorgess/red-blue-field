# Entrega executável 0.4

Esta entrega oferece um laboratório local para estudar segurança com agentes. Os contratos de evidência anteriores preservam suas versões.

## Componentes

| Componente | Estado da entrega |
| --- | --- |
| FieldDesk | Serviço HTTP, banco SQLite e dados isolados por episódio. |
| Controlador | Escopo, identidade, orçamento, prazo, interrupção e revisão vinculada. |
| Agentes | Roteiros fixos e adaptador opcional para modelos compatíveis com OpenAI. |
| Busca | Pilha em profundidade, hipóteses filhas, deduplicação e fronteira pendente. |
| Blue | Observação, quarentena, suspensão, revogação e restauração. |
| Cenários | S01–S18 executáveis; S10 usa grafo lógico. |
| Cloud | S13–S16 e S18 usam emulação local ou `CloudSandboxAdapter` (`cloud_live`) com verificação de teardown. |
| Execução no alvo | S12 usa contêiner descartável, marcador inofensivo e reset/recriação verificada (`/reset`). |
| Ferramentas | Perfis diagnósticos fixos disponíveis ao operador e ao planejador (`tool_profile`) + verificação de grupos de inventário. |
| Painel | Experimentos, traces, hipóteses, decisões, campanhas, revisão e aprendizado. |
| Evidências | Manifesto, cadeia de eventos, artefatos, assinatura externa Ed25519 (`signature.json`), validação e exportação. |
| MCP red e blue | Servidores `stdio` (`rbf-mcp-red`, `rbf-mcp-blue`) e Streamable HTTP (`/mcp/red`, `/mcp/blue`) com autenticação por papel. |

## Estrutura do código

| Arquivo | Responsabilidade |
| --- | --- |
| `red_blue_field/engine.py` | Serviços de aplicação e ciclo dos experimentos. |
| `red_blue_field/api.py` | Interface HTTP de controle, do alvo e Streamable HTTP MCP. |
| `red_blue_field/mcp.py` | Servidores MCP Red e Blue (`2025-11-25`), validação de esquemas e idempotência. |
| `red_blue_field/signing.py` | Geração de chaves Ed25519, assinatura externa e verificação criptográfica de evidências. |
| `red_blue_field/cloud.py` | Adaptador de conta sandbox cloud com separação de 5 papéis, orçamento e verificação de teardown. |
| `red_blue_field/fielddesk.py` | Dados, falhas sintéticas e políticas do alvo. |
| `red_blue_field/tools.py` | Ferramentas permitidas, `tool_profile` no planejador, reset do worker e respostas blue. |
| `red_blue_field/agents.py` | Roteiros e chamadas ao modelo. |
| `red_blue_field/security.py` | Limites, escopo e decisões vinculadas com identidades distintas de revisores. |
| `red_blue_field/evidence.py` | Coleta e validação de evidências. |
| `red_blue_field/utility.py` | Verificações específicas de tarefas legítimas. |
| `red_blue_field/worker.py` | Serviço descartável de execução, perfis diagnósticos e endpoint `/reset`. |
| `red_blue_field/static/` | Painel local, sem dependências externas de interface. |

O Model Context Protocol (MCP) conecta ferramentas aos agentes via `stdio` (`rbf mcp --role red|blue`) e Streamable HTTP (`/mcp/red`, `/mcp/blue`), exigindo tokens específicos por papel (`red` vs `blue`) e validando `inputSchema`, `outputSchema` e chaves de idempotência.

## Limites desta etapa

Os testes padrão usam roteiros conhecidos. Eles demonstram efeitos e controles nos serviços; alegações de robustez de modelos exigem execuções com modelos identificados.

Os testes do intermediário usam um provedor simulado. Eles verificam mensagens, orçamento, falhas e evidências, sem medir um modelo comercial.

A etapa atual dispensa licença Daybreak e acesso ampliado a modelos. Todos os componentes usam recursos comuns do ambiente local.

Os cenários cloud modificam estado do emulador local (`cloud_emulated`) ou usam configuração explícita de sandbox (`RBF_AWS_CONFIG`) validada pelo `CloudSandboxAdapter`.

O FieldDesk compartilha o processo do controlador. Suas falhas controladas afetam dados sintéticos; execução de comandos ocorre somente no contêiner descartável.

O contêiner recebe comandos fixos de ferramenta. Alvos externos, argumentos livres e módulos arbitrários permanecem fora desses perfis.

O blue padrão aplica regras. Com modelo configurado, ele recebe observações autenticadas e escolhe respostas permitidas; o controlador valida cada resposta.

As comparações padrão usam informação parcial e casos conhecidos. Experimentos sobre descoberta inédita exigem famílias separadas e casos de avaliação reservados.

O parecer de aprendizado permanece pendente até a prática humana. Testes automáticos da aplicação comprovam comportamento do software, sem atribuir domínio ao estudante.

## Continuação do estudo

Siga o [guia de execução](running-the-lab.md) e registre os resultados por episódio. Use o [backlog de capacitação](linear-backlog.md) para organizar prática, explicação e reteste.

## Entregas implementadas nesta etapa

1. Servidores MCP red e blue (`red_blue_field/mcp.py`), com autenticação separada por papel, `stdio` e HTTP (`/mcp/red`, `/mcp/blue`).
2. Acesso do planejador aos perfis diagnósticos da bancada (`tool_profile` em `S11` e `S12`), respeitando limites e portão de revisão humana (`Profile D`).
3. Ampliação dos perfis diagnósticos inofensivos e verificação de grupos de inventário (`inventory_groups` em `/tools`).
4. Reset e limpeza verificada dos alvos descartáveis (`/reset`, `reset_worker()`, `RBF_AUTO_RECREATE_WORKERS=1` e `recreate_worker=True` na restauração Blue).
5. Assinatura criptográfica externa Ed25519 (`red_blue_field/signing.py`, `rbf keygen`, `rbf sign`, `POST /api/runs/{run_id}/sign`) e identidades distintas para revisores e avaliadores humanos (`human:<id>`).
6. Adaptador de sandbox cloud (`red_blue_field/cloud.py`) com validação de 5 papéis separados, teto de custo e verificação de teardown (`cloud-teardown.json`).

## Chats externos com Codex

Os [scripts Red e Blue](terminal-agents.md) usam Deep Agents e o protocolo Responses da proxy local existente.

Cada chat registra prompt, plano, ferramentas, respostas e métricas em uma sessão própria. O identificador do episódio liga os dois fluxos.

## Pendências de validação e estudo

1. Executar modelos identificados, dentro dos acessos disponíveis. Os testes atuais do intermediário usam um provedor simulado.
2. Reservar casos inéditos e comparar prática manual, roteiro e agente com repetições suficientes.
3. Medir falsos positivos, perda de utilidade e recuperação em campanhas com modelos.
4. Obter revisão humana externa e concluir o documento final de competências.

## Verificação desta entrega

A execução local passa nos testes automatizados do laboratório, cobrindo fronteiras de segurança, cenários `S01`–`S18`, servidores MCP Red e Blue, assinatura Ed25519, reset de workers, adaptador cloud sandbox e agentes de terminal.
