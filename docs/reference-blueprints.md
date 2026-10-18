# O que construir a partir das duas referências

Plano de construção, não integração já entregue. As versões consultadas em 18/10/2026 estão fixadas no [índice de fontes](../research/sources.json). Os dois projetos têm papéis complementares: execução de pentest e auditoria de código com validação.

## PentAGI: do objetivo à ação observável

O [PentAGI](https://github.com/vxcontrol/pentagi/tree/843dfeb4bfc809c09d1bc5022e567c602d8fc9dd) oferece uma referência de orquestração de pentest com agentes, execução de ferramentas, memória e observabilidade. Seu README distingue pentest autônomo de campanhas BAS predefinidas. A interface documenta relatórios Markdown/PDF; não presumir export de dataset JSON equivalente ao nosso contrato.

| Construção no red-blue-field | Artefato e teste de aceitação |
| --- | --- |
| Planejador pequeno: objetivo → hipótese → tarefa → ação → observação. | IDs causais e histórico de revisões do plano; demonstrar qual observação mudou a próxima ação. |
| Runner de ferramentas separado do planejador. | Versão, comando/script e hash, alvo resolvido, timeout, saída e exit code; efeito conferido pelo avaliador. |
| Checkpoints de supervisão e limites independentes. | Parar por orçamento ou interrupção mesmo quando o modelo insiste em continuar. |
| Memória com origem e separação por campanha. | Identificar que informação foi reutilizada; resetar entre splits para impedir vazamento dos casos reservados. |
| Telemetria ligada a ações e efeitos. | Reconstruir uma tentativa desde a hipótese até o estado do alvo, incluindo falhas e reintentos. |
| Adaptador comparativo opcional do PentAGI. | Mesmo alvo, informação inicial, ferramentas permitidas e orçamento; mapear registros realmente disponíveis e declarar lacunas. |

Começar com o agente próprio; não adotar toda a plataforma como requisito da fundação. A comparação externa só começa após testes independentes de escopo, runner e coleta. A recomendação upstream de separar a execução Docker do host é pertinente, mas não comprova a contenção de nossa futura instalação. Não montar socket Docker do host ou credenciais pessoais no worker. Rever licença das dependências e condições de serviços opcionais antes da integração.

## Cloudflare: da suspeita ao achado verificável

A [security-audit-skill](https://github.com/cloudflare/security-audit-skill/tree/c1c8a8c1471069fb0e188eeaff69b8e8db6564a8) é referência para auditoria orientada por código, cobertura e verificação independente. O fluxo exige rastrear entrada, fronteira, controles e efeito. Sua validação local isolada não é um executor de pentest cloud.

| Construção no red-blue-field | Artefato e teste de aceitação |
| --- | --- |
| Inventário white box do FieldDesk. | Revisão do código, entrypoints, identidades, fronteiras e sinks; comparar com a visão black box sem misturar resultados. |
| Ledger de cobertura por unidade. | `coverage-ledger.json`, com unidades verificadas, pendentes, bloqueadas e fora de escopo; zero achados não significa cobertura total. |
| Separação entre descoberta e validação. | Identificar finder e verifier; o verificador recebe alegação e evidência e reconstrói o caminho sem depender do veredito anterior. |
| Registro estruturado de achados. | `findings.jsonl`: `confirmed`, `needs_validation` ou `rejected`, código e/ou prova runtime, pré-condições e fronteira afetada. |
| Relatório derivado dos registros. | Cada afirmação aponta para achado e evidência; correção e reteste demonstram preservação da tarefa legítima. |
| Revalidação após mudança. | Vincular cobertura e achados ao commit; mudança relevante invalida conclusões anteriores até novo exame. |

Uma suspeita sem verificação independente fica no ledger e torna a auditoria incompleta. `needs_validation` exige caminho já verificado e uma condição decisiva ainda não resolvida, com plano exato de validação; não recebe severidade. `confirmed` exige prova do efeito e pode receber severidade fundamentada no impacto. Endurecimento desejável e vulnerabilidade demonstrada são resultados diferentes.

No laboratório, validação por outra pessoa ou por nova invocação de agente tem identidade e contexto registrados; usar outro contexto do mesmo modelo não garante independência estatística. Essa função é diferente do blue, do revisor de aprovação e do avaliador de efeitos. O relatório explicita as limitações da revisão. Somente o coletor promove artefatos permitidos para o corpus canônico; saída de participante permanece não confiável.

## Entregas e estudo

1. Fundação: contratos de contexto, escopo, cobertura e achados; um episódio completo S01.
2. Pentest local: runner e trilha de planejamento inspirados no PentAGI; S11–S12 manual/script/agente.
3. Auditoria white box: suspeita verdadeira, falso positivo e caso bloqueado; verificação independente, correção e reteste.
4. Comparação opcional com PentAGI: revisão fixada, capacidades equivalentes, custo e lacunas de exportação declarados.
5. Publicação: dataset e estudo que expliquem o que o agente descobriu, o que apenas repetiu e o que o verificador conseguiu confirmar.

Não foi copiado código dessas referências nem executada a skill de auditoria nesta revisão. Os schemas locais são contratos próprios inspirados no método; não prometem compatibilidade com o formato upstream.
