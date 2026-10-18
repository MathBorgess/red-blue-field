# Dataset e traces observáveis

Estado: contrato proposto. Os schemas deste repositório definem formatos de revisão; não representam uma implementação de coleta. Exemplos em `examples/` são ilustrativos, sem ataque executado e sem valor para métricas.

## Evidência obrigatória por execução

Cada execução deverá gerar:

- `manifest.json`: versões de código/modelo/política/cenário, fixture, seed, parâmetros, orçamento e checksums dos artefatos.
- `events.jsonl`: eventos do controlador, red, assistente alvo, políticas, ferramentas, blue, revisão e avaliador, correlacionados por IDs.
- `episodes.jsonl`: rótulos, resultados, custo, utilidade, término e referências de evidência.
- Snapshots inicial/final ou deltas verificáveis da aplicação e ledger do sink.
- Artefatos retornados pelo provedor e ferramentas, com proveniência e versão da transformação de publicação.
- `report.json` e uma síntese legível com denominadores, casos e limitações.

Um episódio com coleta incompleta não será descartado silenciosamente. O controlador preserva o que existe, registra uma falha por canal de supervisão e encerra antes de novas ações com efeito. Se um efeito já puder ter ocorrido, seu resultado fica desconhecido até reconciliação com a aplicação.

## Correlação e origem

Todo evento contém `run_id`, `episode_id`, `event_id`, sequência atribuída pelo coletor, horário UTC, `trace_id`, `span_id`, `parent_span_id`, componente, tipo e referências a artefatos. O esquema guarda horário do evento e de recebimento para identificar atraso.

Spans sugeridos: `episode`, `invoke_agent red`, `invoke_agent target`, `invoke_agent blue`, `model.request`, `tool.execute`, `policy.evaluate`, `approval.wait`, `response.execute` e `evaluate`. Esses nomes são internos propostos; fazer o mapeamento explícito para a revisão fixada das [convenções GenAI](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md). Propagar contexto pelo gateway e pelo executor, inclusive em filas e reintentos.

O coletor obtém a identidade do canal autenticado. Texto de ticket que se pareça com log continua sendo conteúdo de ticket. O red pode escrever nesse conteúdo, mas não pode produzir um evento autenticado de política ou de revisão.

Registrar entradas e saídas efetivamente disponibilizadas pelo provedor, ferramentas propostas e executadas, erros, recusas e resumos estruturados de decisões. Não pressupor acesso ao raciocínio interno do modelo. Um resumo explicativo não substitui evidência da ação.

## Integridade e reconstrução

Somente o coletor escreve a sequência canônica. Para o primeiro marco, um ledger local de escritor único permite revisar ordem e lacunas. Na versão distribuída, usar identificadores idempotentes, sequência de recebimento e links causais; não presumir que relógios distribuídos estabeleçam causalidade.

Gerar hashes dos artefatos, encadear envelopes canônicos dos eventos e selar a lista em um manifesto final fora das áreas graváveis pelos agentes. Um hash sozinho só detecta divergência contra uma referência confiável; não impede que alguém com controle do coletor reescreva arquivo e hash. O modelo de ameaça inicial não concede esse controle aos participantes.

Redação de dados altera os bytes. Exportações públicas devem ter hashes e manifesto próprios e apontar para os IDs lógicos de origem. Não afirmar que um arquivo sanitizado conserva o checksum bruto.

## Visibilidade e dados

| Visão | Conteúdo |
| --- | --- |
| Red | Entradas enviadas, observações permitidas, consumo e resultados locais disponibilizados pelo cenário. |
| Blue | Eventos e alertas filtrados por papel; conteúdo de evidência marcado como não confiável. |
| Avaliador | Estado e ledger completos do episódio, canaries e oráculos reservados. |
| Revisor | Ação exata proposta, efeito previsto, origem dos dados, versão e evidências necessárias para decidir. |
| Publicação | Corpus sintético e exportação transformada, com política de redação e checksums próprios. |

Canaries são fictícios. Credenciais do broker, tokens de aprovação, dados de contas reais, mensagens privadas e logs do host não entram nos artefatos públicos. Guardar somente evidência necessária; preservar os registros do estudo até avaliação humana, sem limpeza automática por idade.

O armazenamento bruto permanece fora do Git. `datasets/releases/<version>/` poderá receber um export sintético revisado, data card, licença definida para aquele material e manifesto. Não reutilizar conteúdo de incidentes ou benchmarks sem verificar a licença específica; referências bibliográficas não transferem direitos sobre datasets.

## Estados e rótulos

`record_kind` separa `illustrative`, `fixture_replay` e `model_run`. Um ensaio com um modelo local e um com API remota informam esse detalhe no manifesto. `outcome` distingue `attacker_success`, `blocked`, `no_effect`, `unknown` e `not_executed`.

`termination_reason` distingue conclusão, recusa do modelo, limite de recursos, decisão humana, interrupção do controlador, erro de infraestrutura e exemplo. Um ataque malsucedido pode ser válido; um episódio inválido não vira defesa bem-sucedida. Resultado adversarial, conclusão da tarefa legítima e qualidade da evidência são campos independentes.

## Reprodução

Fixture, versão, configuração e hashes permitem reconstruir o ensaio. Reexecutar respostas de ferramentas gravadas verifica o pipeline; reconsultar um modelo verifica uma nova amostra. Seed, temperatura zero e mesmo identificador comercial não garantem respostas idênticas, especialmente quando o provedor altera revisões.
