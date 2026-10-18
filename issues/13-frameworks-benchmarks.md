<!-- red-blue-field:RB-013 -->

## Problema e resultado esperado

Aprender integração de frameworks e avaliação externa sem esconder o mecanismo nem confundir diferentes escores.

Dependências: [RB-004 / #4](https://github.com/MathBorgess/red-blue-field/issues/4).

## Escopo

Interface própria primeiro, adaptador CrewAI depois; inventário Radar e benchmarks externos em ambientes/critérios próprios.

## Critérios de aceitação

- [ ] Fixar versões, licenças, dados redistribuíveis e custo de inferência/infra.
- [ ] Executar caso equivalente no laço simples e no CrewAI com mesma informação, permissões e orçamento.
- [ ] Radar gera inventário e testes realmente suportados; registrar limitações por framework.
- [ ] AgentDojo e SafetyBench mantêm resultados separados de FieldDesk/pentest/cloud.
- [ ] Explicar quais riscos e fronteiras cada ferramenta cobre e quais não testa.
- [ ] Novas integrações preservam escopo externo, interrupção e correlação de evidência.

## Verificação

Confirmar capacidades na versão usada. Scan suportado não implica runtime test equivalente; escore comportamental não confirma efeito de infraestrutura.

Referências: [ferramentas](https://github.com/MathBorgess/red-blue-field/blob/main/docs/tooling-and-references.md), [método](https://github.com/MathBorgess/red-blue-field/blob/main/docs/experiment-design.md).
