<!-- red-blue-field:RB-012 -->

## Problema e resultado esperado

Demonstrar como falhas tradicionais e manipulação do agente se encadeiam, sem inferir etapas não observadas.

Dependências: [RB-004 / #4](https://github.com/MathBorgess/red-blue-field/issues/4), [RB-009 / #9](https://github.com/MathBorgess/red-blue-field/issues/9), [RB-011 / #11](https://github.com/MathBorgess/red-blue-field/issues/11).

## Escopo

S16 documento→ação cloud, S17 API de configuração→comportamento e S18 cadeia completa com contenção blue. Implementar S17 local antes de exigir cloud para os demais.

## Critérios de aceitação

- [ ] S16 liga documento não confiável, proposta do assistente, identidade e drift confirmado.
- [ ] S17 confirma alteração não autorizada de configuração e efeito na tarefa posterior.
- [ ] S18 prova cada transição serviço/agente/cloud e registra onde a defesa interrompeu a cadeia.
- [ ] Ablação separa guardrail do modelo, política de ferramenta, autorização do serviço e IAM.
- [ ] Desvio de comportamento sem efeito posterior é rótulo próprio, sem alegação de comprometimento cloud.
- [ ] Blue registra sinal, contenção, restauração e dano residual; mantém limites externos constantes.

## Verificação

Tarefas e controles benignos pareados; acesso e recursos do contrato anterior. Uma cadeia sem prova de uma transição permanece não demonstrada.

Referências: [cenários](https://github.com/MathBorgess/red-blue-field/blob/main/docs/scenarios.md), [arquitetura](https://github.com/MathBorgess/red-blue-field/blob/main/docs/architecture.md), [experimento](https://github.com/MathBorgess/red-blue-field/blob/main/docs/experiment-design.md).
