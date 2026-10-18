# Etapa cloud: efeitos reais em recursos do laboratório

O objetivo é medir acesso, privilégio, configuração, disponibilidade e recuperação em recursos próprios. O serviço do provedor e a infraestrutura que o opera não são o alvo.

## Preparação e progressão

1. Reproduzir a hipótese em serviço local real e, quando útil, em emulação.
2. Selecionar serviço e região; revisar documentação, permissões, custos e regras do provedor para aquele teste.
3. Preparar conta sandbox separada, sem dados ou vínculos de produção; emitir o contrato para recursos exatos.
4. Provisionar por infraestrutura como código e conferir o estado inicial, a coleta e a interrupção.
5. Executar manual, script e agente com identidade/capacidades comparáveis.
6. Conferir efeito, conter com blue, restaurar e verificar teardown por um papel separado.

Essa sequência não assume que uma emulação reproduz IAM ou a política de rede real.

## Superfícies e provas

| Cenário | Efeito planejado | Evidência independente |
| --- | --- | --- |
| S13: IAM/armazenamento | Identidade da fixture alcança marcador que sua política pretendida deveria proteger. | Políticas e identidade efetivas, leitura confirmada e auditoria do recurso. |
| S14: rede | Regra do recurso de teste muda e altera conectividade dentro da rede do laboratório. | Estado antes/depois e sondagem de alcance de uma origem autorizada. |
| S15: disponibilidade | Configuração ou operação permitida na arena interrompe uma função e depois é restaurada. | Healthcheck de referência, eventos da alteração e retorno da função. |
| S16/S18: cadeia híbrida | Manipulação do agente ou falha de API provoca uma operação cloud indevida na fixture. | Sequência causal, sessão usada, chamada aceita e efeito no recurso. |

Um papel pode ter permissões excessivas dentro da arena para permitir estudar a falha. A identidade externa de provisionamento e contenção permanece separada. Validar suporte de condições e escopo de recurso por ação; não depender apenas de prefixo ou tag.

## Políticas do provedor e disponibilidade

A [política de pentest da AWS](https://aws.amazon.com/security/penetration-testing/) distingue avaliações de recursos do cliente, serviços permitidos, atividades excluídas e casos que exigem revisão, como determinados eventos adversariais/C2. Conferir a versão aplicável antes do ensaio; propriedade da conta não autoriza qualquer atividade.

A trilha padrão não inclui flooding ou DoS cloud. Indisponibilidade será estudada por configuração/ação controlada do recurso e, quando apropriado, [AWS FIS](https://docs.aws.amazon.com/fis/latest/userguide/what-is.html). Uma falha acionada pelo controlador valida resposta e recuperação; não prova que o agente descobriu um caminho ofensivo. Rotular a origem do efeito.

Serviços gerenciados têm restrições próprias de entrada/saída para ferramentas de avaliação. O executor ofensivo não será colocado automaticamente em AgentCore ou em API Gateway; escolher o runtime depois de verificar a política aplicável.

## Identidade, custo e auditoria

Usar sessões temporárias no broker/adaptador, sem inserir credenciais reais em prompts, arquivos públicos ou exemplos. A fixture pode expor tokens sintéticos; segredos operacionais não são rótulos de sucesso.

Separar provisionamento, participante, blue, observação e restauração. Coleta deve cobrir as chamadas relevantes, incluindo eventos de dados e logs do banco quando necessários. Preservar IDs de requisição e versões de configuração; redigir identificadores sensíveis na exportação mantendo a correlação lógica.

Estimar inferência, máquinas, rede, armazenamento e logs. Aplicar quotas, limites de duração, restrição de criação e watchdog; alertas de billing têm atraso e não garantem um teto financeiro. Registrar custo conhecido, estimativa e custo ainda não reconciliado separadamente.

## Experimentos de guardrails

O filtro do [Bedrock Guardrails](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html) e as permissões [IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html) protegem fronteiras diferentes. Conferir proposta do modelo, autorização e efeito, em vez de concluir segurança a partir do texto filtrado.

Na camada gerenciada, verificar a oferta atual: a documentação consultada informa que [Bedrock Agents Classic](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html) está em manutenção e fechado a novos clientes, e aponta para [AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html). AgentCore e inferência têm cobrança por uso; esta trilha não pressupõe gratuidade.

Nenhum recurso cloud foi provisionado ou testado nesta revisão.
