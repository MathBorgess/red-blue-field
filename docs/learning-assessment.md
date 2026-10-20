# Aprendizado, supervisão e validação de domínio

Revisão 0.3. Este plano define o marco final do estudo. As competências continuam pendentes de avaliação. Model Context Protocol (MCP) conecta ferramentas aos agentes.

## Entrega principal

Produzir um documento final de aprendizado, supervisão e intervenção humana. O documento deverá ligar cada conclusão a episódios e artefatos verificáveis.

Usar o [modelo de relatório](final-learning-report-template.md). Preencher resultados somente após executar os testes e revisar a evidência.

## Competências e provas

| Competência | Prova do estudante | Evidência |
| --- | --- | --- |
| Fundamentos | Explicar requisições, rede, identidade e autorização; reproduzir acesso legítimo e indevido. | Desenho de fronteiras e prova manual S01. |
| Ferramentas PentAGI | Escolher ferramenta, conferir sintaxe e interpretar seus limites. | Comparação manual/script/agente com versões e efeitos. |
| Pentest local | Encontrar e explicar acesso ao banco e execução limitada. | S11–S12, correção e reteste. |
| Segurança de agentes | Testar objetivo, ferramentas, memória e autonomia. | S02–S09 e controles benignos. |
| Hipóteses | Formular refutação, expandir evidências e encerrar ramos sem suporte. | Árvore com três níveis, refutação, repetição e pendências. |
| Cloud | Interpretar permissões, provar mudança e restaurar recurso. | S13–S15 com auditoria e teardown. |
| Blue | Investigar, conter e recuperar sem apagar perdas anteriores. | Comparação B/C e efeito da resposta. |
| MCP | Conectar, testar e explicar autorização dos dois servidores. | Dois clientes por servidor e provas de separação de papéis. |
| Auditoria | Distinguir hipótese, falso positivo e achado confirmado. | Cobertura e verificação independente. |
| Supervisão humana | Justificar aceite, recusa, alteração e parada. | Operação exata, decisão, tempo e efeito. |
| Comunicação | Explicar risco, causa e correção para outra pessoa. | Relatório revisado e resposta aos comentários. |

O [referencial NICE — competências em cibersegurança](https://www.nist.gov/itl/applied-cybersecurity/nice/nice-framework-resource-center/nice-framework-current-versions) orienta a descrição de tarefas, conhecimentos e habilidades.

Esta rubrica pertence ao projeto. Seu uso organiza a avaliação; certificação profissional exige seus próprios critérios.

## Rubrica

| Nível | Evidência necessária |
| --- | --- |
| `not_assessed` | Competência ainda sem avaliação concluída. |
| 1 — guiado | Conclui com roteiro ou ajuda direta; explica parte do mecanismo. |
| 2 — independente | Explica, reproduz, corrige e retesta sem roteiro pronto. |
| 3 — transferência | Resolve variante inédita e justifica limites e alternativas. |

Separar desempenho do agente e desempenho do estudante. Registrar assistência recebida e contribuição manual em cada tarefa.

O marco de domínio exige nível 2 em todas as competências obrigatórias. A avaliação inédita deve demonstrar nível 3 nas frentes selecionadas.

Competências com evidência insuficiente permanecem pendentes. O responsável registra lacuna, ação corretiva e novo teste.

## Prova final

1. Receber três casos reservados: serviço, agente e cloud.
2. Receber ao menos um caso sem falha ou com evidência insuficiente.
3. Formular hipóteses e refutações antes dos testes.
4. Executar uma parte manual e outra com assistência do agente.
5. Demonstrar investigação blue, contenção e recuperação previstas.
6. Conectar os dois MCPs e explicar identidade, capacidades e limites.
7. Corrigir a causa ou orientar uma correção concreta; conferir o reteste.
8. Defender as conclusões perante o revisor humano responsável.

Casos reservados ficam separados das famílias usadas para ajustar agentes. O agente recebe somente as observações permitidas ao papel.

## Marco de supervisão e intervenção

Comparar C, com blue, e D, com revisão humana. Preservar tarefa, ambiente, modelo e limites para interpretar a contribuição da pessoa.

| Momento | O que registrar |
| --- | --- |
| Antes do teste | Hipótese, risco, ação proposta, alternativas e informação disponível ao revisor. |
| Decisão | Identidade do revisor, aceite/recusa/alteração/parada, justificativa e versão da operação. |
| Execução | Consumo da aprovação, chamada efetiva e eventual mudança de parâmetros. |
| Depois | Efeito observado, utilidade, contenção, recuperação e perdas residuais. |
| Avaliação | Intervenção necessária, intervenção indevida, tempo humano e limitação da conclusão. |

Revisor simulado testa o protocolo. Pessoa real avalia julgamento humano; registrar resultados dessas modalidades separadamente.

Uma mudança posterior ao aceite invalida a decisão anterior. O agente pede nova revisão da operação exata quando a política exigir.

## Conclusão do estudo

O revisor humano decide por competência: domínio demonstrado, parcial ou pendente. A conclusão cita as provas e delimita sua aplicação.

Produzir cinco a dez estudos de portfólio a partir das execuções. Preservar resultados negativos e limites de cobertura.

As práticas corporativas fora do laboratório exigirão experiência adicional. O documento deverá identificar essas lacunas, incluindo especialidades ainda fora do currículo.
