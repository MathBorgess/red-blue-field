# Issues e dependências — revisão 0.2

Publicadas e conferidas em 18/10/2026. São 16 issues: a pesquisa inicial concluída e 15 fatias abertas de revisão, implementação e estudo. Sete novas issues ampliam o plano para pentest local/cloud, cadeias híbridas, ferramentas, portfólio, auditoria white box e comparação opcional com PentAGI.

| ID | Issue | Estado na publicação | Dependências |
| --- | --- | --- | --- |
| RB-001 | [#1 — Pesquisa: consolidar fontes, limites de evidência e dez cenários](https://github.com/MathBorgess/red-blue-field/issues/1) | Concluída | Nenhuma |
| RB-002 | [#2 — Spec: AI Pentest, Agentic Red Teaming e estudo dos limites de defesa](https://github.com/MathBorgess/red-blue-field/issues/2) | Aberta | [#1](https://github.com/MathBorgess/red-blue-field/issues/1) |
| RB-003 | [#3 — Fundação: executar episódio S01 em API real com escopo e evidência](https://github.com/MathBorgess/red-blue-field/issues/3) | Aberta | [#2](https://github.com/MathBorgess/red-blue-field/issues/2) |
| RB-004 | [#4 — Agentes: laço transparente red/alvo e prompt injection S02](https://github.com/MathBorgess/red-blue-field/issues/4) | Aberta | [#3](https://github.com/MathBorgess/red-blue-field/issues/3) |
| RB-005 | [#5 — MVP: avaliar envenenamento de metadados de ferramentas (S03)](https://github.com/MathBorgess/red-blue-field/issues/5) | Aberta | [#4](https://github.com/MathBorgess/red-blue-field/issues/4) |
| RB-006 | [#6 — MVP: implementar agente blue e comparar detecção e contenção](https://github.com/MathBorgess/red-blue-field/issues/6) | Aberta | [#4](https://github.com/MathBorgess/red-blue-field/issues/4) |
| RB-007 | [#7 — MVP: implementar revisão humana e aprovação vinculada à ação (S04)](https://github.com/MathBorgess/red-blue-field/issues/7) | Aberta | [#3](https://github.com/MathBorgess/red-blue-field/issues/3), [#6](https://github.com/MathBorgess/red-blue-field/issues/6) |
| RB-008 | [#8 — Estudo: campanhas por frente, dataset, traces e limites dos guardrails](https://github.com/MathBorgess/red-blue-field/issues/8) | Aberta | [#5](https://github.com/MathBorgess/red-blue-field/issues/5), [#6](https://github.com/MathBorgess/red-blue-field/issues/6), [#7](https://github.com/MathBorgess/red-blue-field/issues/7), [#9](https://github.com/MathBorgess/red-blue-field/issues/9), [#10](https://github.com/MathBorgess/red-blue-field/issues/10), [#15](https://github.com/MathBorgess/red-blue-field/issues/15) |
| RB-009 | [#9 — Agentic core: memória, tool misuse, loops e evidência hostil S05–S09](https://github.com/MathBorgess/red-blue-field/issues/9) | Aberta | [#4](https://github.com/MathBorgess/red-blue-field/issues/4) |
| RB-010 | [#10 — Pentest local: API/banco, execução limitada e runner observável S11–S12](https://github.com/MathBorgess/red-blue-field/issues/10) | Aberta | [#3](https://github.com/MathBorgess/red-blue-field/issues/3) |
| RB-011 | [#11 — Cloud lab: IAM, armazenamento, rede e disponibilidade S13–S15](https://github.com/MathBorgess/red-blue-field/issues/11) | Aberta | [#10](https://github.com/MathBorgess/red-blue-field/issues/10) |
| RB-012 | [#12 — Híbrido: serviço → comportamento do agente → cloud S16–S18](https://github.com/MathBorgess/red-blue-field/issues/12) | Aberta | [#4](https://github.com/MathBorgess/red-blue-field/issues/4), [#9](https://github.com/MathBorgess/red-blue-field/issues/9), [#11](https://github.com/MathBorgess/red-blue-field/issues/11) |
| RB-013 | [#13 — Ferramentas: CrewAI, Radar, AgentDojo e Agent-SafetyBench](https://github.com/MathBorgess/red-blue-field/issues/13) | Aberta | [#4](https://github.com/MathBorgess/red-blue-field/issues/4) |
| RB-014 | [#14 — Portfólio: publicar 5–10 estudos com provas, correções e retestes](https://github.com/MathBorgess/red-blue-field/issues/14) | Aberta | [#8](https://github.com/MathBorgess/red-blue-field/issues/8) |
| RB-015 | [#15 — Auditoria: cobertura e verificador independente inspirados na Cloudflare](https://github.com/MathBorgess/red-blue-field/issues/15) | Aberta | [#3](https://github.com/MathBorgess/red-blue-field/issues/3) |
| RB-016 | [#16 — Comparação opcional: adaptador PentAGI com escopo e evidência comuns](https://github.com/MathBorgess/red-blue-field/issues/16) | Aberta | [#10](https://github.com/MathBorgess/red-blue-field/issues/10), [#15](https://github.com/MathBorgess/red-blue-field/issues/15) |

O [manifesto](manifest.json) conserva o recibo e aponta para os corpos idênticos aos publicados. O estado atual pertence ao GitHub. A issue #1 preserva a entrega inicial no snapshot 0.1; memória e autonomia passam ao núcleo em #9. O blueprint PentAGI orienta #4/#10/#16; o método Cloudflare está em #15. Publicar este backlog não executa campanhas nem provisiona cloud.

A sequência prioriza fundação → agente e pentest local → memória/defesa/auditoria → campanha local. Cloud e cadeias híbridas são etapas posteriores; as comparações de frameworks e PentAGI não bloqueiam a fundação. [Trilha de estudo](../docs/study-plan.md) e [spec](../SPEC.md) detalham os critérios.
