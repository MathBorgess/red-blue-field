# red-blue-field — segurança com agentes

Laboratório para aprender pentest, testes adversariais de agentes, defesa e supervisão humana.

**Revisão 0.3 · 20/10/2026**. Estado: pesquisa, especificações e contratos. Aplicação, agentes e servidores aguardam implementação.

## Entregas finais previstas

| Entrega | Resultado esperado |
| --- | --- |
| FieldDesk e arena | Serviços vulneráveis próprios, agente interno e recursos cloud efêmeros. |
| Agentes red/blue | Investigação por hipóteses, ataque limitado, defesa, contenção e recuperação. |
| Ferramentas PentAGI | Adaptadores por perfil, versões verificadas e prova de efeito. |
| MCP red | Servidor conectável aos agentes do usuário para pentest e agentic red teaming. |
| MCP blue | Servidor conectável para investigação, defesa e contenção. |
| Dataset e traces | Hipóteses, ferramentas, efeitos, defesa e decisões humanas observáveis. |
| Documento final | Aprendizado, intervenções, provas de domínio e lacunas avaliadas por pessoa responsável. |

Model Context Protocol (MCP) é um protocolo para conectar ferramentas a agentes. O servidor aplica escopo e permissões em cada chamada.

## Como vamos estudar

1. Construir o primeiro episódio completo e reproduzi-lo manualmente.
2. Integrar ferramentas e comparar execução manual, script e agente.
3. Explorar hipóteses em profundidade com evidência, refutação e orçamento.
4. Testar objetivo, ferramentas, memória e autonomia do agente interno.
5. Medir defesa e intervenção humana sem apagar perdas anteriores.
6. Reproduzir casos cloud no sandbox e comprovar restauração.
7. Entregar os MCPs e resolver casos inéditos de avaliação.
8. Publicar o documento final com parecer humano e estudos verificáveis.

Os dezoito cenários cobrem pentest de serviços, segurança de agentes e cadeias híbridas. Cada execução declara seu ambiente e suas limitações.

## Especificações e estudo

- [Spec principal](SPEC.md) e [backlog no Linear](docs/linear-backlog.md).
- [Ferramentas PentAGI](docs/pentagi-tools.md) e [inventário estruturado](research/pentagi-tool-inventory.json).
- [Busca por hipóteses](docs/hypothesis-search.md) e [contratos MCP red/blue](docs/mcp-red-blue.md).
- [Aprendizado e supervisão](docs/learning-assessment.md) e [modelo do documento final](docs/final-learning-report-template.md).
- [Trilha prática](docs/study-plan.md), [cenários](docs/scenarios.md) e [catálogo](scenarios/catalog.json).
- [Arquitetura base](docs/architecture.md), [escopo](docs/lab-scope.md) e [etapa cloud](docs/cloud-lab.md).
- [Desenho experimental](docs/experiment-design.md), [observabilidade](docs/observability.md) e [validação](docs/validation.md).
- [Pesquisa](docs/research.md), [fontes](research/sources.json) e [blueprints PentAGI/Cloudflare](docs/reference-blueprints.md).
- [Issues históricas do GitHub](issues/README.md), [portfólio](docs/portfolio-plan.md) e [vocabulário](GLOSSARY.md).

## Evidência e contenção

O avaliador confere efeitos no serviço, banco, processo ou recurso cloud. Relatos dos agentes constituem alegações até a verificação.

O controlador fixa recursos, identidades, ações, prazo e orçamento. A busca por hipóteses preserva esse limite em cada ramo.

Replay, serviço local, emulação cloud e cloud real têm rótulos distintos. Exemplos ilustrativos permanecem fora das métricas.

O documento final avaliará competências demonstradas. Seu modelo conserva resultados e notas pendentes até a revisão humana.
