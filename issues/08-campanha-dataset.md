<!-- red-blue-field:RB-008 -->

## Problema e resultado esperado

Uma demonstração isolada não permite comparar defesa, custo ou utilidade. Executar uma campanha congelada dos quatro cenários do MVP, publicar métricas com denominadores e produzir uma release sintética verificável.

Dependências: [RB-005 / #5](https://github.com/MathBorgess/red-blue-field/issues/5), [RB-006 / #6](https://github.com/MathBorgess/red-blue-field/issues/6), [RB-007 / #7](https://github.com/MathBorgess/red-blue-field/issues/7).

## Critérios de aceitação

- [ ] Tamanho do piloto, modelos, orçamento e configurações são fixados antes da campanha.
- [ ] Comparações A/B, B/C e C/D preservam pares e identificam o controle responsável pelo efeito.
- [ ] Desenvolvimento e teste reservado são separados por linhagem de ataque, incluindo paráfrases.
- [ ] Ataques fixos e adaptativos são analisados separadamente com orçamento explícito.
- [ ] Relatório inclui sucessos, falhas, recusas, interrupções, inválidos e desconhecidos.
- [ ] Medir utilidade, falso bloqueio, detecção, contenção, recuperação e custo total conhecido.
- [ ] Demonstrar restauração do serviço sem ocultar exposições já registradas no sink.
- [ ] Export contém somente dados sintéticos, data card, licença definida e hashes próprios após transformação.
- [ ] Exemplos ilustrativos e revisores simulados não contam como resultados medidos de modelo ou pessoa real.
- [ ] Um leitor consegue reconstruir pelo menos um sucesso adversarial e um bloqueio a partir dos artefatos.

## Verificação

Validar contratos, sequência, correlação, referências de evidência e checksums. Publicar contagens e limites da amostra. A proposta inicial de 80 episódios adversariais e 80 controles é um desenho exploratório, sujeito a revisão antes de qualquer gasto; não é medição ou compromisso de execução.

Referências: [protocolo](https://github.com/MathBorgess/red-blue-field/blob/main/docs/experiment-design.md), [exportação](https://github.com/MathBorgess/red-blue-field/blob/main/docs/observability.md).
