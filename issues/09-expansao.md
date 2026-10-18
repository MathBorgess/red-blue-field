<!-- red-blue-field:RB-009 -->

## Problema e resultado esperado

Memória e autonomia passam ao currículo principal, sem esperar a campanha final. Implementar cenários que revelem persistência, abuso de capacidade e interrupção.

Dependências: [RB-004 / #4](https://github.com/MathBorgess/red-blue-field/issues/4).

## Escopo

S05–S09 são entregas incrementais. S10 permanece pesquisa opcional em grafo lógico, fora da conclusão do núcleo.

## Critérios de aceitação

- [ ] S05 tem duas etapas no mesmo episódio, proveniência de memória e reset entre episódios.
- [ ] S06 mede ferramenta indevida e recuperação preservando efeito anterior.
- [ ] S07 mede crescimento de chamadas, loops, teto de recursos e revogação fora do modelo.
- [ ] S08 injeta texto hostil observado pelo blue, sem permitir escrita no coletor autenticado.
- [ ] S09 usa sentinela local que representa destino fora do contrato; nenhum terceiro é sondado.
- [ ] Cada cenário tem controle benigno, hipótese, budget congelado, oráculo e rótulos por camada.
- [ ] Se selecionado depois, S10 muda apenas estados de grafo finito, sem propagação de processos/pesos.

## Verificação

Reproduzir mecanismo, corrigir, retestar e explicar limites. Tarefa impossível dentro do contrato deve terminar sem alegação falsa de sucesso.

Referências: [catálogo](https://github.com/MathBorgess/red-blue-field/blob/main/scenarios/catalog.json), [trilha](https://github.com/MathBorgess/red-blue-field/blob/main/docs/study-plan.md).
