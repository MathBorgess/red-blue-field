# red-blue-field — AI Pentest & Agentic Red Teaming

Projeto de referência para aprender a construir agentes, usar agentes em pentest, atacar o comportamento de agentes e verificar defesa e recuperação com evidência reproduzível.

**Revisão 0.2 · 18/10/2026:** pesquisa, especificação e contratos. Aplicação, runners e agentes ainda não implementados; nenhum pentest ou recurso cloud foi executado nesta revisão.

## Três frentes de estudo

| Frente | O que é atacado | O que precisa ser provado |
| --- | --- | --- |
| Pentest com agentes | APIs, banco, serviços executáveis e configurações cloud do laboratório. | Acesso ou efeito indevido confirmado no alvo, com contribuição do agente comparada a execução manual e scripts. |
| Agentic red teaming | Objetivo, ferramentas, memória, delegação, aprovações e autonomia do agente interno. | Desvio observável de tarefa e chamadas propostas/executadas, mesmo quando outra camada impede o dano. |
| Cadeias híbridas | Caminhos entre serviço vulnerável, agente interno e recursos cloud. | Cada transição da cadeia, permissões efetivas, efeito final e resposta blue. |

O FieldDesk continua como aplicação fictícia central. O laboratório acrescenta APIs e banco vulneráveis executáveis, worker descartável para provas de execução e recursos cloud efêmeros. IAM, regras de rede e disponibilidade são parte do currículo.

## Progressão

1. Construir e explicar um agente simples, suas ferramentas, identidade e memória.
2. Executar o mesmo teste manualmente, com script e com agente.
3. Confirmar uma invasão em serviços locais próprios e corrigir a falha.
4. Desviar o agente interno por entradas e ferramentas, testar memória e ciclos.
5. Reproduzir casos selecionados em cloud sandbox e observar mudanças reais de configuração.
6. Encadear as duas frentes, conter com blue e medir recuperação.
7. Publicar dataset, traces e estudos técnicos sustentados por execuções.

Replay, serviço local real, emulação cloud e cloud real terão rótulos separados. O currículo avança por evidência e compreensão do mecanismo.

## Leitura

- [Spec e critérios de aceitação](SPEC.md) · [issue de revisão #2](https://github.com/MathBorgess/red-blue-field/issues/2).
- [Arquitetura e fronteiras](docs/architecture.md) · [escopo de cada laboratório](docs/lab-scope.md).
- [18 cenários](docs/scenarios.md) · [catálogo estruturado](scenarios/catalog.json).
- [Experimentos e métricas](docs/experiment-design.md) · [dataset e traces](docs/observability.md).
- [Trilha de aprendizado](docs/study-plan.md) · [ferramentas e referências verificadas](docs/tooling-and-references.md).
- [O que construir com referências do PentAGI e da skill da Cloudflare](docs/reference-blueprints.md).
- [Etapa cloud](docs/cloud-lab.md) · [oito estudos de portfólio planejados](docs/portfolio-plan.md).
- [Pesquisa de casos](docs/research.md) · [fontes públicas](research/sources.json) · [vocabulário](GLOSSARY.md).
- [Issues e dependências](issues/README.md) · [validação documental](docs/validation.md).

## Limite sob teste e contenção

Guardrails do modelo, permissões de ferramentas, autorização da aplicação e políticas cloud serão testadas separadamente e em composição. O controle externo de escopo permanece fixo: protege host, coletor e recursos fora do episódio, sem corrigir antecipadamente a falha intencional do alvo.

As provas usam ambientes próprios, dados sintéticos e efeitos recuperáveis dentro do contrato do episódio. Em cloud, conta/região/recursos, regras do provedor, orçamento e teardown são definidos antes da execução. A publicação deste plano não provisiona recursos ou autoriza gasto.

## Evidência por execução

Manifesto e escopo versionados, ferramentas propostas e executadas, logs do alvo, auditoria cloud quando aplicável, estados antes/depois, veredito independente e relatório. Ausência de execução, recusa do modelo, limite de orçamento e falha de infraestrutura são resultados diferentes.

Uma mudança de comportamento não prova invasão de serviço. Uma chamada aceita não prova alteração efetiva. O relatório deve demonstrar o efeito e identificar a camada que bloqueou ou falhou.
