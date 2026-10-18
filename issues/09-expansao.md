<!-- red-blue-field:RB-009 -->

## Problema e resultado esperado

Após o piloto, selecionar quais riscos justificam novos experimentos. Os candidatos S05–S10 cobrem memória, uso indevido de ferramentas, esgotamento de recursos, evidência hostil, limite de escopo e propagação em grafo finito.

Dependência: RB-008.

## Critérios de aceitação

- [ ] Identificar falha ou pergunta não respondida pelo MVP antes de selecionar o próximo cenário.
- [ ] Para cada cenário escolhido, fixar hipótese, capacidade red, visão blue, controles benignos, orçamento e oráculo.
- [ ] Preservar o envelope de isolamento em todos os perfis.
- [ ] S05 tem duas etapas no mesmo episódio e reset entre episódios.
- [ ] S08 usa conteúdo hostil observado, sem escrita do atacante no coletor confiável.
- [ ] S09 usa somente sentinela controlado; nenhum endereço de terceiro é testado.
- [ ] S10 altera estados de um grafo limitado, sem copiar pesos ou executar propagação real.
- [ ] Novas medições têm manifesto, traces e rótulos comparáveis aos do piloto.

Não é uma obrigação de implementar os seis cenários ao mesmo tempo. A escolha depende do resultado e do aprendizado do piloto.

Referência: [cenários de expansão](https://github.com/MathBorgess/red-blue-field/blob/main/docs/scenarios.md).
