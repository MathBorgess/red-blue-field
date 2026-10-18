<!-- red-blue-field:RB-004 -->

## Problema e resultado esperado

O replay determinístico não mede como um modelo escolhe ferramentas ou reage a dados hostis. Integrar os agentes red e alvo por um broker de inferência e executar S02, mantendo os mesmos oráculos por efeito.

Dependência: [RB-003 / #3](https://github.com/MathBorgess/red-blue-field/issues/3).

## Escopo

O red pode alterar apenas as superfícies sintéticas previstas no cenário. O assistente alvo atende uma tarefa legítima. A variante indireta usa documento recuperado; uma variante direta preserva a mesma intenção para comparação. A saída de dados usa somente um sink local.

## Critérios de aceitação

- [ ] Provedor, modelos, revisões, parâmetros e teto de gasto são definidos antes de chamadas reais.
- [ ] Somente o broker possui a credencial; os participantes não têm HTTP genérico ou shell.
- [ ] Red recebe feedback permitido, sem acesso ao canary reservado ou ao veredito oculto.
- [ ] O efeito é medido no sink e na resposta entregue; recusa tardia não apaga saída parcial.
- [ ] Perfil B aplica identidade, capacidades e fluxo de origem/destino fora do LLM.
- [ ] Chamadas, recusas, erros, tentativas descartadas e consumo conhecido aparecem nos traces.
- [ ] `fixture_replay` e `model_run` são identificados separadamente nos dados.

## Verificação

Comparar tarefa legítima, entrada hostil direta e documento hostil, com mesmo alvo e orçamento. Confirmar cada alegação no estado, sem usar o relato do red ou do alvo como rótulo. Fixar a configuração antes do conjunto reservado.

Referências: [S02 e controles](https://github.com/MathBorgess/red-blue-field/blob/main/docs/scenarios.md), [desenho experimental](https://github.com/MathBorgess/red-blue-field/blob/main/docs/experiment-design.md).
