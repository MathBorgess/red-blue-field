# red-blue-field

Laboratório de estudo de cybersecurity e de defesa de sistemas com agentes de IA. A proposta reúne uma aplicação fictícia, um agente red team e um agente blue team. Cada execução deverá produzir evidências do ataque, da defesa e do efeito observado na aplicação.

**Estado em 18/10/2026:** pesquisa e desenho experimental. A aplicação, os agentes e o executor ainda não foram implementados. Não há resultados experimentais nem dataset de ataques executados nesta revisão.

## O que queremos descobrir

- Quais falhas vêm da aplicação, das permissões, do modelo ou da composição das ferramentas?
- Quanto uma defesa determinística resolve antes da participação do blue team?
- Quando o agente de defesa melhora detecção, contenção e recuperação?
- Em quais ações a intervenção humana muda o resultado, e com qual custo?
- Conseguimos reconstruir cada conclusão a partir de eventos e do estado do sistema?

## Leitura

1. [Pesquisa e limites das evidências](docs/research.md).
2. [Cenários hipotéticos](docs/scenarios.md) e [catálogo estruturado](scenarios/catalog.json).
3. [Arquitetura proposta](docs/architecture.md).
4. [Desenho experimental e métricas](docs/experiment-design.md).
5. [Dataset, traces e publicação](docs/observability.md).
6. [Trilha de estudo](docs/study-plan.md).
7. [Vocabulário](GLOSSARY.md) e [fontes primárias](research/sources.json).
8. [Spec produzida com to-spec, para avaliação](SPEC.md).
9. [Issues, critérios de aceitação e dependências](issues/README.md).

## Primeiro recorte proposto

O **FieldDesk** é um help desk fictício com dois tenants, tickets, documentos públicos e internos, reembolsos simulados e uma caixa de saída local. Seu assistente de produto é o alvo das manipulações por linguagem. Ele é um componente da aplicação; o blue team é um defensor separado.

O MVP cobre autorização entre tenants, prompt injection, envenenamento de metadados de ferramentas e aprovação humana. Os outros cenários entram depois de validar isolamento, coleta de evidência e avaliação independente.

O red team pode variar entradas e sequências de ações dentro do cenário. O blue team observa eventos permitidos e propõe ou executa respostas limitadas. Um controlador fora dos agentes impõe escopo, orçamento e interrupção; um avaliador separado verifica o efeito real. O isolamento é constante em todos os grupos experimentais.

## O que conta como execução

Uma execução só será considerada válida com manifesto, eventos correlacionados, estado inicial/final e veredito verificável. Tentativas interrompidas e falhas de infraestrutura também serão registradas. Exemplos de formato deverão ser identificados como ilustrativos e nunca entrar no cálculo das métricas.

O repositório público receberá apenas dados sintéticos e exportações revisadas. O desenho usa ferramentas locais específicas e não depende de conectores com contas reais.

## Publicação

Repositório público: [MathBorgess/red-blue-field](https://github.com/MathBorgess/red-blue-field). O backlog fica em [GitHub Issues](https://github.com/MathBorgess/red-blue-field/issues); pesquisa, spec e contratos são versionados junto do projeto. A publicação das propostas não constitui execução dos experimentos.
