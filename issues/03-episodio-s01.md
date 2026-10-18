<!-- red-blue-field:RB-003 -->

## Problema e resultado esperado

Ainda não existe uma execução que ligue tentativa adversarial, efeito na aplicação e evidência. Implementar uma fatia completa de S01 com adaptadores determinísticos: inicializar o FieldDesk fictício, tentar acesso entre tenants e produzir dataset e trace verificáveis.

Dependência: [RB-002 / #2](https://github.com/MathBorgess/red-blue-field/issues/2).

## Escopo

Dois tenants, tickets com canaries sintéticos, tarefa legítima, perfil vulnerável A e perfil protegido B. Incluir controlador de prazo/orçamento, gateway, coletor e avaliador independente. A defesa e o perfil vulnerável compartilham o mesmo isolamento externo.

## Critérios de aceitação

- [ ] Um comando inicia fixture limpa e executa o episódio completo.
- [ ] A tarefa legítima funciona nos dois perfis.
- [ ] A leitura entre tenants tem efeito confirmado no perfil intencionalmente vulnerável e é negada antes do efeito no perfil protegido.
- [ ] Manifesto, eventos, snapshots, ledger e veredito validam os contratos propostos.
- [ ] Falha de coleta encerra novas ações e preserva resultado desconhecido quando houver efeito não reconciliado.
- [ ] Prazo e orçamento são aplicados fora dos agentes; sentinela controlado verifica isolamento.
- [ ] O processo usa dados sintéticos e não recebe credenciais ou diretórios pessoais do host.

## Verificação

Testar pela execução completa do episódio e conferir respostas e estado do banco. Rodar caso legítimo, violação conhecida, orçamento esgotado e coletor interrompido. Os agentes ainda podem ser adaptadores determinísticos; não atribuir esse replay a comportamento de LLM.

Referências: [arquitetura](https://github.com/MathBorgess/red-blue-field/blob/main/docs/architecture.md), [observabilidade](https://github.com/MathBorgess/red-blue-field/blob/main/docs/observability.md).
