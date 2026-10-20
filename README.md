# red-blue-field — segurança com agentes

Laboratório executável para aprender pentest, testes adversariais de agentes, defesa e supervisão humana.

**Revisão 0.4 · 20/10/2026**. Aplicação, painel, cenários, agentes, evidências e testes locais disponíveis.

## Começar

Requer Python 3.12 e Docker Compose.

```bash
git clone https://github.com/MathBorgess/red-blue-field.git
cd red-blue-field
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
rbf init
docker compose up --build -d
```

Abra `http://127.0.0.1:8080` e use `RBF_CONTROL_TOKEN`, criado no arquivo `.env`.

Crie S01 no perfil A, execute e baixe as evidências. Repita no perfil B para comparar a autorização por cliente.

O [guia de execução](docs/running-the-lab.md) explica modos, ferramentas, revisão humana, campanhas e relatórios.

Os [chats Red e Blue](docs/terminal-agents.md) usam Deep Agents e sua proxy local do Codex em dois terminais.

Eles incluem prompts editáveis, planos visíveis e logs separados de mensagens, ferramentas, latência e tokens informados.

## Dois terminais: Red e Blue

Instale os chats no ambiente virtual e gere a configuração privada, caso ela ainda esteja ausente:

```bash
. .venv/bin/activate
pip install -e '.[chat]'
test -f .env || rbf init
```

`rbf init` cria `.env` a partir de [.env.example](.env.example), com tokens aleatórios. Se `.env` já existe, preserve seus tokens.

Nesse arquivo, preencha `RBF_CODEX_MODEL` com um modelo disponível na sua conta. Confira `RBF_CODEX_PROXY_URL` e `RBF_FIELD_URL`.

Mantenha o Field via Docker Compose e sua proxy Codex em execução. Os chats leem `.env` como configuração, sem executar shell.

No terminal Red:

```bash
python scripts/red_teamer.py --verbose
```

O Red cria um episódio, mostra `RUN_ID=...` e salva o identificador em `artifacts/private/active-run.json`.

No terminal Blue:

```bash
python scripts/blue_teamer.py --verbose
```

O Blue lê o mesmo arquivo e confere o episódio no servidor. As conversas ficam separadas.

## Consultar e escolher o run_id

O `run_id` identifica um episódio. Cada novo episódio recebe seu próprio valor; `.env.example` conserva esse campo vazio.

Para consultar o identificador selecionado:

```bash
python -m json.tool artifacts/private/active-run.json
```

Para escolher um episódio específico:

```bash
python scripts/red_teamer.py --run-id IDENTIFICADOR --verbose
python scripts/blue_teamer.py --run-id IDENTIFICADOR --verbose
```

Troque `IDENTIFICADOR` pelo valor real mostrado pelo Red. `--run-id` tem prioridade sobre `RBF_RUN_ID` e o arquivo local.

O Red cria um episódio quando `RBF_RUN_ID` fica vazio. O Blue consulta o arquivo local quando falta uma seleção explícita.

Cada seleção Red atualiza o arquivo local. Para experimentos simultâneos, escolha `--run-id` ou arquivos distintos com `--run-file CAMINHO`.

Episódios encerrados permanecem disponíveis no painel para consulta. Crie outro episódio para continuar os testes.

## Comandos e experimentos

| Comando | Efeito |
| --- | --- |
| `/allow` | Habilita ações somente para a próxima mensagem. |
| `/metrics` | Mostra chamadas, tokens informados, latências e erros da sessão. |
| `/reset` | Limpa a memória da conversa; preserva logs e alvo. |
| `/finish` | Conclui o episódio e gera o dataset. Afeta ambos os terminais. |
| `/stop` | Interrompe o episódio. Afeta ambos os terminais. |
| `/quit` | Fecha o chat e preserva o prazo do episódio. |

Para executar os dois roteiros, um após o outro:

```bash
python scripts/red_teamer.py --experiment --allow-actions --verbose
python scripts/blue_teamer.py --experiment --allow-actions --verbose
```

Os logs ficam em `artifacts/private/chats/PAPEL/SESSAO/`. Eles incluem `session.json`, `events.jsonl`, `metrics.json`, `latest-request.json` e `latest-response.json`.

Argumentos têm prioridade sobre variáveis exportadas; estas têm prioridade sobre `.env`. Use `--env-file CAMINHO` para selecionar outra configuração.

O token exportado em `RBF_CONTROL_TOKEN` prevalece sobre o arquivo de token selecionado.

Para uso por agentes, consulte o [guia de agentes](AGENTS.md). O [guia dos chats](docs/terminal-agents.md) explica prompts, ferramentas, evidências e limites.

## O que está pronto

| Componente | Entrega |
| --- | --- |
| FieldDesk | Serviço local, banco SQLite, documentos, assistente e dados sintéticos por episódio. |
| Controle | Escopo, identidades, limites, interrupção e aprovação vinculada. |
| Agentes | Roteiros sem modelo e intermediário opcional compatível com OpenAI. |
| Cenários | Dezoito casos de serviços, agentes e cadeias híbridas. |
| Defesa | Regras blue, resposta opcional por modelo, contenção e restauração. |
| Ferramentas | Nmap, sqlmap e seis perfis auxiliares dentro do contêiner. |
| Evidências | Dataset JSONL, traces correlacionados, estados, manifesto e exportação verificável. |
| Aprendizado | Registro de explicação, evidências, ajuda, lacunas e intervenções humanas. |

O experimento funciona sem licença Daybreak e sem acesso ampliado a modelos. Os alvos ficam no laboratório local.

Os roteiros fixos testam casos conhecidos. Execuções com modelo exigem endereço, identificação e preços configurados; seus registros recebem rótulo próprio.

O [estado da implementação](docs/implementation-status.md) detalha limites e componentes. A etapa cloud usa emulação local; S12 usa alvo Docker descartável.

Os servidores do Model Context Protocol (MCP) red e blue ficam para a próxima entrega. Seus contratos e serviços internos já estão separados.

## Estudo e referências

- [Spec principal](SPEC.md) e [backlog no Linear](docs/linear-backlog.md).
- [Ferramentas PentAGI](docs/pentagi-tools.md) e [inventário estruturado](research/pentagi-tool-inventory.json).
- [Busca por hipóteses](docs/hypothesis-search.md) e [contratos MCP](docs/mcp-red-blue.md).
- [Aprendizado e supervisão](docs/learning-assessment.md) e [modelo do documento final](docs/final-learning-report-template.md).
- [Trilha prática](docs/study-plan.md), [cenários](docs/scenarios.md) e [catálogo](scenarios/catalog.json).
- [Desenho experimental](docs/experiment-design.md), [observabilidade](docs/observability.md) e [validação](docs/validation.md).
- [Pesquisa](docs/research.md), [fontes](research/sources.json) e [referências PentAGI/Cloudflare](docs/reference-blueprints.md).
- [Issues históricas](issues/README.md), [portfólio](docs/portfolio-plan.md) e [vocabulário](GLOSSARY.md).

Os testes verificam comportamento do software. Uma pessoa responsável avaliará seu domínio com prática, explicação, correção e reteste documentados.
