<!-- red-blue-field:RB-008 -->

## Problema e resultado esperado

Medir capacidade ofensiva, proteção, utilidade e recuperação com evidência e denominadores completos, em releases incrementais.

Dependências: [RB-005 / #5](https://github.com/MathBorgess/red-blue-field/issues/5), [RB-006 / #6](https://github.com/MathBorgess/red-blue-field/issues/6), [RB-007 / #7](https://github.com/MathBorgess/red-blue-field/issues/7), [RB-009 / #9](https://github.com/MathBorgess/red-blue-field/issues/9), [RB-010 / #10](https://github.com/MathBorgess/red-blue-field/issues/10), [RB-015 / #15](https://github.com/MathBorgess/red-blue-field/issues/15).

## Escopo

Piloto S01–S04 continua calibração; lotes de memória/autonomia, pentest local e auditoria têm desenho próprio. Cloud/híbrido só após suas issues; frameworks e PentAGI entram como comparações opcionais quando disponíveis.

## Critérios de aceitação

- [ ] Congelar tamanho, oráculos, revisão, modelo, configuração, orçamento e regra de parada antes de cada lote.
- [ ] Separar frente, ambiente e black/gray/white box; não somar emulação e cloud real.
- [ ] Comparar manual/script/agente com capacidades equivalentes; declarar roteiros conhecidos e informação inicial.
- [ ] A/B mede pacote de controles; B/C e C/D isolam acréscimos; ablação varia uma camada interna por vez.
- [ ] Separar desenvolvimento e reservado por linhagem; resetar memória entre famílias e splits.
- [ ] Publicar sucessos, bloqueios, recusas, inválidos, desconhecidos e falhas de infraestrutura.
- [ ] Medir utilidade, falso bloqueio, descoberta confirmada, cobertura, detecção, contenção, recuperação e custo humano/modelo/infra.
- [ ] Export sintético inclui data card, licença, manifesto, escopo e hashes próprios; remover segredos e dados privados.
- [ ] Reconstituir sucesso adversarial e bloqueio a partir da evidência; exemplos não contam como métricas.

## Verificação

Validar contratos e efeitos reais; preservar resultados negativos e limitações. A proposta 80 adversariais + 80 controles é estimativa do piloto agêntico, não compromisso de executar todo o produto nessa amostra.

Referências: [protocolo](https://github.com/MathBorgess/red-blue-field/blob/main/docs/experiment-design.md), [observabilidade](https://github.com/MathBorgess/red-blue-field/blob/main/docs/observability.md), [portfólio](https://github.com/MathBorgess/red-blue-field/blob/main/docs/portfolio-plan.md).
