# Exemplo de contrato, não de resultado

Estes arquivos foram montados para revisar o formato. **Nenhum ataque, defesa, aplicação ou modelo foi executado.** Todos os registros têm `record_kind: illustrative`, e o episódio tem `outcome: not_executed`. As medições são nulas.

O fluxo hipotético mostra uma solicitação entre tenants, uma possível decisão de bloqueio e um possível alerta. Ele não demonstra que uma implementação detectou ou bloqueou a tentativa.

- [Manifesto](manifest.json): formatos, limitações e checksums dos arquivos.
- [Eventos](events.jsonl): envelopes correlacionados e cadeia de hashes de exemplo.
- [Episódio](episodes.jsonl): classificação explícita de não execução.
- [Escopo](scope.json): contrato ilustrativo, sem identidade ou alvo operacional, com checksum no manifesto.

Os contratos são da revisão 0.2. O contexto declara replay ilustrativo; nenhum campo representa prova de desvio, comprometimento ou drift cloud. Não há achados nem ledger de auditoria neste exemplo, pois nenhuma auditoria foi feita.

O hash de cada evento é o SHA-256 do JSON UTF-8 sem o campo `event_hash`, com chaves ordenadas, sem espaços separadores, sem números não finitos e com caracteres Unicode preservados. `prev_event_hash` participa do hash. Para tipos numéricos e codificações em outros runtimes, definir canonicalização interoperável antes da coleta distribuída.

Uma exportação futura terá seu próprio manifesto e hashes depois da transformação. Um exemplo ilustrativo deve ser excluído de qualquer cálculo de eficácia.
