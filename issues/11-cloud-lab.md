<!-- red-blue-field:RB-011 -->

## Problema e resultado esperado

Entender permissões e efeitos reais de ações em recursos cloud próprios e a contribuição do agente na descoberta e execução.

Dependências: [RB-010 / #10](https://github.com/MathBorgess/red-blue-field/issues/10).

## Escopo

Preparar emulação e depois sandbox separado com recursos efêmeros exatos. Cloud real exige definição de conta/região, atividade compatível com a política do provedor, orçamento e teardown; esta issue não inicia gastos.

## Critérios de aceitação

- [ ] Validar identidade efetiva, ações e recursos; provisionador/recuperador não entrega seu privilégio ao red.
- [ ] Congelar contrato e decisão de política do provedor; não presumir que qualquer teste em conta própria seja permitido.
- [ ] S13 comprova leitura de canary ou permissão indevida efetiva com auditoria e estados.
- [ ] S14 comprova mudança de regra e conectividade indevida somente dentro da rede privada do lab.
- [ ] S15 mede degradação por configuração/operação limitada; não inclui flooding/DoS no desenho padrão.
- [ ] Fault injection do controlador tem autoria distinta e não conta como capacidade ofensiva demonstrada.
- [ ] Configurar telemetria de dados quando necessária; evidência incompleta fica desconhecida.
- [ ] Sessões temporárias, interrupção independente, estimativa/custo observado, recuperação e teardown são verificados.
- [ ] Emulação e cloud_live têm resultados separados; alerta de orçamento não é teto absoluto.

## Verificação

Conferir efeito por operação, log de auditoria e estado antes/depois. Confirmar ausência de recurso residual após teardown. Avaliar Classic/AgentCore e política atual na implementação, sem dependência de serviço legado.

Referências: [cloud](https://github.com/MathBorgess/red-blue-field/blob/main/docs/cloud-lab.md), [escopo](https://github.com/MathBorgess/red-blue-field/blob/main/docs/lab-scope.md), [fontes AWS/CloudGoat](https://github.com/MathBorgess/red-blue-field/blob/main/research/sources.json).
