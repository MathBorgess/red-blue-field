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
