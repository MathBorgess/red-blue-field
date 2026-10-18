<!-- red-blue-field:RB-003 -->

## Problema e resultado esperado

Implementar a primeira fatia completa: API FieldDesk executável, banco sintético, tentativa entre tenants e veredito pelo efeito real.

Dependências: [RB-002 / #2](https://github.com/MathBorgess/red-blue-field/issues/2).

## Escopo

Dois tenants, perfil vulnerável A e protegido B, gateway, controlador e coletor separados. Manual e script podem preceder o uso de modelo.

## Critérios de aceitação

- [ ] Um comando prepara fixture limpa e executa tarefa legítima e violação conhecida nos dois perfis.
- [ ] Leitura do canary é confirmada no serviço vulnerável e bloqueada antes do efeito no protegido.
- [ ] Escopo versionado contém identidade, recursos, ações, destinos, prazo, orçamento, interrupção e recuperação.
- [ ] Manifesto, eventos, snapshots e veredito validam contratos 0.2; serviço real sem LLM é tool_run, replay continua fixture_replay.
- [ ] Falha do coletor suspende novas ações; efeito possível sem reconciliação fica unknown.
- [ ] Sentinela controlado verifica contenção externa; participantes não recebem credencial administrativa nem diretório pessoal do host.
- [ ] Contexto registra frente, ambiente, modo ofensivo, acesso e controles; hashes e referências resolvem.

## Verificação

Conferir resposta e banco por avaliador separado. Exercitar tarefa limpa, violação, orçamento esgotado e coleta interrompida. Isso não demonstra descoberta por agente.

Referências: [arquitetura](https://github.com/MathBorgess/red-blue-field/blob/main/docs/architecture.md), [escopo](https://github.com/MathBorgess/red-blue-field/blob/main/docs/lab-scope.md), [evidência](https://github.com/MathBorgess/red-blue-field/blob/main/docs/observability.md).
