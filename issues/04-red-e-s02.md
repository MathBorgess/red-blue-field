<!-- red-blue-field:RB-004 -->

## Problema e resultado esperado

Construir um agente compreensível e observar como escolhe ferramentas e reage a entrada hostil, antes de adotar uma plataforma maior.

Dependências: [RB-003 / #3](https://github.com/MathBorgess/red-blue-field/issues/3).

## Escopo

Red, assistente interno e broker separados. S02 direto/indireto com sink local; nenhuma ferramenta shell nesta fatia.

## Critérios de aceitação

- [ ] Explicar e registrar objetivo, hipótese, tarefa, ação, observação e revisão do plano.
- [ ] Definir modelo, revisão, parâmetros e orçamento antes de chamadas reais; broker conserva credenciais.
- [ ] Red recebe só superfícies e feedback permitidos, sem oráculo/canary reservado.
- [ ] Canary é verificado no sink/saída; recusa tardia não apaga vazamento parcial.
- [ ] Comparar controles internos por ablação e manter contenção externa constante.
- [ ] Separar desvio do modelo, ação proposta, bloqueio do executor e efeito no alvo.
- [ ] Model_run, tool_run e replay permanecem distinguíveis; falhas e consumo entram no trace.

## Verificação

Tarefa legítima, entrada direta hostil e documento hostil pareados. Fixar contexto e orçamento; verificar efeito fora da narrativa dos agentes.

Referências: [S02](https://github.com/MathBorgess/red-blue-field/blob/main/docs/scenarios.md), [referência de planejador PentAGI](https://github.com/MathBorgess/red-blue-field/blob/main/docs/reference-blueprints.md), [experimento](https://github.com/MathBorgess/red-blue-field/blob/main/docs/experiment-design.md).
