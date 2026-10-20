# Dataset e traces observáveis

Revisão documental 0.3. Coleta e execução aguardam implementação. Os exemplos ilustram formatos e permanecem fora das métricas.

## Artefatos por episódio

| Artefato | Conteúdo |
| --- | --- |
| `manifest.json` | Código, modelo, cenário, configuração, orçamento, escopo e checksums. |
| `scope.json` | Recursos, identidades, ações, destinos, validade, interrupção e recuperação. |
| `events.jsonl` | Propostas, chamadas, políticas, defesa, revisão e efeitos. |
| `episodes.jsonl` | Veredito, validade, utilidade, custo e razão de término. |
| `hypotheses.jsonl` | Pais, fonte, refutação, testes, evidências e estado da busca. |
| Estados e deltas | Serviço, banco, processo, configuração cloud e ledger da saída. |
| `coverage-ledger.json` e `findings.jsonl` | Cobertura de auditoria e achados com verificação independente, quando aplicável. |
| `report.json` | Resultados, denominadores, casos, custo e limitações. |
| Documento de aprendizado | Competências, intervenções, provas e parecer humano. |

## Correlação e origem

Cada evento liga execução, episódio, sequência, horário, ator e artefatos. Traços e spans permitem reconstruir chamadas entre componentes.

O coletor obtém a identidade do canal autenticado. Conteúdo de ticket permanece dado observado, mesmo quando imita um registro de política.

Registrar entradas e saídas disponíveis, ferramentas propostas e executadas, erros e decisões estruturadas. Essas decisões explicam o fluxo observado.

O provedor poderá omitir detalhes internos do modelo. A evidência principal continua sendo a ação e seu efeito no alvo.

Propagar contexto em filas e reintentos. Usar a revisão fixada das [convenções de agentes](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md).

## Hipóteses, servidores e supervisão

A busca em profundidade grava nós e relações conforme o [contrato de hipótese](../schemas/hypothesis.schema.json). O manifesto usa `kind: other` para esse artefato.

Usar eventos `plan.revised` com identificadores de hipótese no payload. Chamadas, decisões e efeitos continuam com seus eventos próprios.

Os servidores do Model Context Protocol (MCP) acrescentam identidade do cliente, operação, perfil e chave de idempotência à correlação.

Cada intervenção registra o revisor, a operação exata, a informação disponível e a justificativa. Registrar também o tempo humano e o efeito posterior.

Separar revisor simulado e pessoa real. O parecer final de domínio pertence ao revisor humano responsável.

## Integridade e falhas

Somente o coletor escreve os registros canônicos. Agentes gravam artefatos candidatos em áreas próprias; o coletor valida e promove arquivos permitidos.

Encadear envelopes canônicos dos eventos e gerar hashes dos artefatos. O manifesto final permanece fora da área gravável pelos participantes.

Hashes detectam divergência contra uma referência confiável. A autenticidade também depende do canal, da identidade e da proteção do coletor.

Na versão distribuída, usar identificadores idempotentes, ordem de recebimento e relações causais. Relógios podem divergir entre máquinas.

Se a coleta falhar, suspender novas ações. Preservar estado, reconciliar efeitos possíveis e manter resultado desconhecido quando faltar prova.

## Visões e publicação

| Papel | Visão |
| --- | --- |
| Red | Entradas enviadas, observações permitidas, ferramentas e consumo próprio. |
| Blue | Sinais e contexto defensivo, com origem e confiança do conteúdo. |
| Avaliador | Estado, canaries e oráculos reservados. |
| Revisor | Operação, identidade, parâmetros, versão, risco e evidências para decidir. |
| Publicação | Exportação sintética, revisada e com checksums próprios. |

Guardar dados brutos fora do Git. Publicar somente dados sintéticos e artefatos revisados, com licença e política de redação definidas.

Credenciais operacionais e conversas privadas permanecem fora da exportação. Preservar correlação por aliases estáveis quando houver identificadores sensíveis.

Uma transformação altera os bytes. Gerar novo manifesto e novos hashes para a exportação pública.

Conservar registros até avaliação humana. A política de retenção deve preservar evidências necessárias e decisões de limpeza.

## Estados e contratos

| Campo | Interpretação |
| --- | --- |
| `record_kind` | `illustrative`, `fixture_replay`, `tool_run` ou `model_run`. |
| `outcome` | Sucesso adversarial, bloqueio, ausência de efeito, desconhecido ou sem execução. |
| `study_context` | Frente, ambiente, modo ofensivo, acesso, variante de proteção e contenção externa. |
| `effect_assessment` | Desvio de comportamento, comprometimento de serviço, mudança cloud e recuperação. |
| `termination_reason` | Conclusão, recusa, orçamento, decisão humana, controlador, infraestrutura ou exemplo. |

Um ataque malsucedido pode produzir um episódio válido. Um episódio inválido permanece distinto de defesa bem-sucedida.

Manifesto e episódios devem concordar no contexto. Registrar rótulos e denominadores separados para replay, serviço local, emulação e cloud real.

O diretório [schemas](../schemas) contém nove contratos. Oito permanecem em 0.2; o contrato de hipótese usa 0.3.

Os schemas conferem estrutura. O validador semântico futuro conferirá referências, identidade dos verificadores, ordem causal, validade do escopo e evidências de cobertura.

O método de [auditoria](reference-blueprints.md) exige prova runtime e remediação proposta para `confirmed`. Somente achados confirmados recebem severidade.

`needs_validation` exige verificação independente, condição decisiva pendente e plano específico. Candidatos sem verificação permanecem no ledger; `rejected` conserva a refutação.

## Reprodução

Fixar código, configuração, fixture, ferramentas e respostas gravadas. Reproduzir respostas registradas verifica o pipeline; consultar o modelo novamente produz outra amostra.

Seed e temperatura ajudam a descrever o ensaio. Mudanças do provedor e variação do modelo limitam a reprodução exata.
