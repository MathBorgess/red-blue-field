<!-- red-blue-field:RB-016 -->

## Problema e resultado esperado

Comparar o agente próprio a uma plataforma de pentest sem atribuir ganhos a ferramentas, acesso ou soluções privilegiadas.

Dependências: [RB-010 / #10](https://github.com/MathBorgess/red-blue-field/issues/10), [RB-015 / #15](https://github.com/MathBorgess/red-blue-field/issues/15).

## Escopo

Adaptador experimental e opcional do PentAGI contra fixtures próprias. Só após runner, escopo e coleta verificados; não substituir toda a fundação pela stack upstream.

## Critérios de aceitação

- [ ] Fixar commit upstream, licença do core/dependências e serviços opcionais usados.
- [ ] Validar contenção, rede, interrupção e limite de recursos fora do agente; não expor host/socket/credenciais pessoais.
- [ ] Mapear registros/API efetivamente disponíveis a plano, tarefa, ação, saída e efeito.
- [ ] Não presumir export JSON equivalente ao nosso dataset a partir de relatórios Markdown/PDF.
- [ ] Mesmo alvo, informação inicial, ferramentas e orçamento; diferenças inevitáveis aparecem na comparação.
- [ ] Resetar memória entre famílias; separar descoberta de roteiro conhecido e confirmar achados pelo verificador.
- [ ] Publicar custo, falhas, recusas e lacunas de telemetria; não reutilizar números de desempenho upstream como resultado nosso.

## Verificação

Episódios local_live com artefatos e contexto próprios. Confirmar que toda alegação do relatório aponta para efeito observado; declarar indisponibilidades em vez de fabricar compatibilidade.

Referências: [PentAGI → construção](https://github.com/MathBorgess/red-blue-field/blob/main/docs/reference-blueprints.md), [protocolo](https://github.com/MathBorgess/red-blue-field/blob/main/docs/experiment-design.md).
