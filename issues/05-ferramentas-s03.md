<!-- red-blue-field:RB-005 -->

## Problema e resultado esperado

Descrições de ferramentas podem carregar instruções adversariais sem uma mudança explícita nas permissões. Executar S03 com um registro local de ferramentas e comparar catálogo aprovado com metadados alterados.

Dependência: [RB-004 / #4](https://github.com/MathBorgess/red-blue-field/issues/4).

## Critérios de aceitação

- [ ] Cada catálogo e descrição apresentados ao modelo têm versão e hash registrados.
- [ ] O red altera somente os metadados permitidos pela fixture.
- [ ] Mudança de descrição não concede novas capacidades ao executor.
- [ ] O perfil protegido suspende catálogo inesperado e preserva a consulta legítima com catálogo aprovado.
- [ ] Trace distingue ferramenta proposta, decisão de política, ferramenta executada e efeito observado.
- [ ] A comparação conserva modelo alvo, tarefa, fixture e orçamento.

## Verificação

Executar o episódio com catálogo limpo, alterado e restaurado. Conferir efeitos e utilidade; um detector que apenas reconhece uma frase fixa não encerra o critério. Reservar variantes de apresentação para a avaliação final.

Referências: [pesquisa sobre tool poisoning](https://github.com/MathBorgess/red-blue-field/blob/main/docs/research.md), [catálogo S03](https://github.com/MathBorgess/red-blue-field/blob/main/scenarios/catalog.json).

## Revisão 0.2

Aplicar os contratos de contexto/efeitos 0.2 e manter o controle sob teste separado da contenção externa. Guardrail do modelo, autorização da ferramenta e autorização do serviço têm resultados separados.
