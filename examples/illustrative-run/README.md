# Exemplo de contrato e formato

Estes arquivos ilustram os contratos. Aplicação, modelos, ataque e defesa continuam sem execução neste exemplo.

Todos os registros têm `record_kind: illustrative`. O episódio e a hipótese usam `not_executed`; os campos de medição permanecem nulos.

O fluxo hipotético representa uma solicitação entre clientes, uma possível decisão e um alerta. A demonstração descreve formato; implementação e eficácia aguardam testes.

- [Manifesto](manifest.json): versões, limitações e checksums.
- [Eventos](events.jsonl): envelopes correlacionados e cadeia de hashes.
- [Episódio](episodes.jsonl): classificação de ausência de execução.
- [Escopo](scope.json): recursos fictícios e limites ilustrativos.
- [Hipótese](hypotheses.jsonl): raiz sem teste ou evidência observada.

O contrato de hipótese usa 0.3. Os contratos anteriores permanecem em 0.2. O manifesto inclui os hashes de todos os artefatos.

## Canonicalização ilustrada

O campo `event_hash` usa `SHA-256` sobre o envelope serializado em `JSON UTF-8`.

1. Excluir `event_hash` do envelope antes da serialização.
2. Ordenar as chaves e excluir espaços separadores.
3. Preservar caracteres Unicode e aceitar apenas números finitos.
4. Incluir `prev_event_hash` no cálculo.

Definir canonicalização interoperável antes da coleta distribuída. Tipos numéricos e codificações podem variar entre runtimes.

Cada exportação transformada terá manifesto e hashes próprios. Os exemplos permanecem fora dos cálculos de eficácia.
