<!-- red-blue-field:RB-006 -->

## Problema e resultado esperado

Precisamos medir o que um agente defensor acrescenta à política determinística. Implementar o blue como participante separado, com view de telemetria limitada e respostas de contenção previstas no perfil C.

Dependência: RB-004.

## Escopo

Investigar alertas e contexto permitido. Respostas possíveis: revogar sessão de teste, suspender ferramenta e colocar documento em quarentena. Alterar código, conceder permissão ou mudar a política durante a medição fica fora desta fatia.

## Critérios de aceitação

- [ ] Blue não recebe intenção red, oráculos, canaries reservados ou estado completo do avaliador.
- [ ] Origem do evento é autenticada pelo canal, e conteúdo de evidência permanece dado não confiável.
- [ ] Momento de recebimento do sinal, decisão e efeito da resposta são registrados.
- [ ] Bloqueios já feitos pelo executor são atribuídos à política, sem crédito indevido ao blue.
- [ ] Comparação B/C mede detecção, contenção, utilidade, falso bloqueio e custo com o mesmo orçamento.
- [ ] Blue não pode desativar coletor, avaliador ou controlador.
- [ ] Uma evidência hostil de controle não concede autoridade ao defensor.

## Verificação

Usar incidentes e controles benignos pareados. Distinguir prevenção antes do efeito de contenção posterior. Conferir revogação ou quarentena no componente que aplica a medida, sem aceitar apenas a frase do agente.

Referências: [fronteiras](https://github.com/MathBorgess/red-blue-field/blob/main/docs/architecture.md), [métricas](https://github.com/MathBorgess/red-blue-field/blob/main/docs/experiment-design.md).
