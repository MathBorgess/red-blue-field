<!-- red-blue-field:RB-007 -->

## Problema e resultado esperado

Uma mensagem de aprovação não garante que a pessoa revisou a ação que será executada. Implementar o fluxo de revisão e S04, vinculando a decisão a uma operação específica de reembolso fictício.

Dependências: RB-003, RB-006.

## Critérios de aceitação

- [ ] Revisor vê identidade, ação, parâmetros, versão, origem dos dados e efeito previsto.
- [ ] Decisão contém prazo e uso único e é vinculada à versão da política e do recurso.
- [ ] Verificação e consumo da aprovação ocorrem atomicamente com o efeito.
- [ ] Aprovação falsa, expirada, reutilizada ou incompatível não produz transação.
- [ ] Retries concorrentes de uma ação autorizada produzem um único efeito.
- [ ] Revisor simulado e pessoa real têm rótulos e métricas distintos.
- [ ] Espera, aceite, recusa e reconfirmação aparecem no trace; segredos de assinatura não aparecem.
- [ ] Revisão acontece antes do efeito e não pode ser substituída por texto do agente.

## Verificação

Testar externamente os efeitos do episódio. Acrescentar teste menor para corrida no consumo e idempotência, além de alteração de valor, destinatário e versão depois do aceite. Dimensionar participação humana em estudo separado, sem atribuir desempenho humano ao revisor simulado.

Referências: [aprovação e recuperação](https://github.com/MathBorgess/red-blue-field/blob/main/docs/architecture.md), [S04](https://github.com/MathBorgess/red-blue-field/blob/main/docs/scenarios.md).
