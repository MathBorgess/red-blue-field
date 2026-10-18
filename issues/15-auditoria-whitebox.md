<!-- red-blue-field:RB-015 -->

## Problema e resultado esperado

Evitar que suspeitas de código ou relatos do agente sejam publicados como vulnerabilidades confirmadas.

Dependências: [RB-003 / #3](https://github.com/MathBorgess/red-blue-field/issues/3).

## Escopo

Aplicar o método da Cloudflare como referência para auditoria white box da revisão autorizada do FieldDesk. Não executar testes cloud por essa skill; o backend de laboratório tem contrato próprio.

## Critérios de aceitação

- [ ] Inventário liga entrypoints, identidades, fronteiras, controles e sinks ao commit auditado.
- [ ] Coverage ledger informa unidades planejadas, verificadas, candidatas, bloqueadas e fora de escopo.
- [ ] Finder e verifier têm identidades/contextos distintos; registrar evidência da verificação e suas limitações.
- [ ] Achado confirmed exige rastreio e prova runtime limitada, impacto, severidade e remediação proposta.
- [ ] Needs_validation exige caminho independentemente verificado e condição decisiva pendente com plano; sem severidade.
- [ ] Candidato sem verificação fica só no ledger e deixa auditoria incompleta; rejeição tem razão.
- [ ] Relatório deriva de registros estruturados; promoção de artefatos canônicos pertence ao coletor.
- [ ] Demonstrar falha real, falso positivo, validação bloqueada e correção/reteste; mudança de commit exige revalidação.

## Verificação

Validar schemas e regras semânticas (incluindo finder diferente do verifier e referências reais). Conferir leitura de código com controle mais forte existente e efeito no alvo; não equiparar hardening desejável a vulnerabilidade.

Referências: [blueprint Cloudflare](https://github.com/MathBorgess/red-blue-field/blob/main/docs/reference-blueprints.md), [achado](https://github.com/MathBorgess/red-blue-field/blob/main/schemas/finding.schema.json), [cobertura](https://github.com/MathBorgess/red-blue-field/blob/main/schemas/coverage-ledger.schema.json).
