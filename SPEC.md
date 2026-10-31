# red-blue-field — especificação de estudo e implementação

> **Documento histórico de 20/10/2026.** Partes sobre chats, modelos e MCP descrevem planos anteriores. Para a organização e os limites atuais, consulte [README](README.md) e [estado da implementação](docs/implementation-status.md).

Revisão **0.4 · 20/10/2026**. Estado: aplicação local executável, cenários e evidências. Os servidores de integração pertencem à próxima etapa.

## Problem Statement

Queremos aprender segurança com agentes de inteligência artificial. O estudo deve ligar hipótese, ferramenta, efeito, defesa e decisão humana.

Precisamos distinguir descoberta de falha, execução de roteiro e alegação sem prova. O estudante deverá explicar o mecanismo e reproduzir os resultados.

O aprendizado inclui serviços tradicionais, comportamento de agentes e recursos cloud próprios. A avaliação precisa preservar tarefas legítimas e reconhecer evidência insuficiente.

## Solution

Construir o FieldDesk, aplicação fictícia com dois clientes isolados, documentos, banco e assistente interno. A etapa atual inclui serviços descartáveis e emulação cloud.

O experimento funciona sem licença Daybreak ou acesso ampliado a modelos. Exercícios usam alvos locais próprios, dados sintéticos e escopo controlado.

| Frente | Alvo e prova |
| --- | --- |
| Pentest com agentes | Serviços, banco e permissões; confirmar acesso ou execução indevida no alvo. |
| Agentic red teaming | Objetivo, ferramentas, memória e autonomia; observar desvio e efeito por camada. |
| Cadeia híbrida | Serviço, agente e cloud; comprovar cada transição e identidade. |

Preparar os serviços internos para dois servidores do Model Context Protocol (MCP). Esse protocolo conecta ferramentas aos agentes do usuário.

Conforme o pedido atual, os dois servidores ficam fora desta entrega. Seus contratos permanecem como requisito da etapa seguinte.

O servidor red oferecerá pentest e testes adversariais de agentes. O servidor blue oferecerá investigação, defesa, contenção e recuperação.

Uma hipótese inicial poderá vir da OWASP — comunidade que publica guias de segurança. Evidências avaliadas poderão originar hipóteses filhas.

A busca seguirá cada ramo em profundidade, com orçamento e controle externo de escopo. O relatório final avaliará aprendizado e supervisão humana.

## User Stories

1. Como estudante, quero explicar o ciclo do agente, para compreender suas decisões.
2. Como estudante, quero repetir testes manualmente, para verificar meu domínio.
3. Como estudante, quero comparar script e agente, para medir sua contribuição.
4. Como pentester, quero inventariar serviços permitidos, para definir hipóteses.
5. Como pentester, quero testar autorização, para confirmar isolamento entre clientes.
6. Como pentester, quero provar acesso indevido ao banco, para explicar a causa.
7. Como pentester, quero confirmar execução limitada, para distinguir efeito de relato.
8. Como estudante, quero entender cada ferramenta do PentAGI, para escolher testes adequados.
9. Como red, quero testar documentos e ferramentas, para observar desvio do agente.
10. Como red, quero testar memória, para medir influência entre tarefas.
11. Como red, quero testar autonomia, para observar repetição e revogação.
12. Como red, quero encadear hipóteses, para investigar evidências novas.
13. Como red, quero registrar refutação, para abandonar caminhos sem suporte.
14. Como pesquisador, quero limitar a profundidade, para tornar campanhas comparáveis.
15. Como pesquisador, quero separar conhecimento prévio, para medir descoberta.
16. Como usuário, quero conectar o MCP red, para avaliar meus sistemas autorizados.
17. Como usuário, quero conectar o MCP blue, para investigar e conter incidentes.
18. Como operador, quero separar identidades red e blue, para limitar cada papel.
19. Como operador, quero emitir escopo, para restringir recursos e ações.
20. Como operador, quero interromper processos, para encerrar ações persistentes.
21. Como blue, quero observar sinais autenticados, para investigar com origem verificável.
22. Como blue, quero conter sessões e ferramentas, para limitar o incidente.
23. Como blue, quero restaurar recursos, para medir recuperação e perdas residuais.
24. Como revisor, quero examinar a ação exata, para decidir antes do efeito.
25. Como revisor, quero invalidar parâmetros alterados, para preservar minha decisão.
26. Como estudante, quero estudar permissões cloud, para comparar intenção e capacidade efetiva.
27. Como avaliador, quero conferir estado e registros, para classificar efeitos.
28. Como auditor, quero verificar achados independentemente, para reduzir falsos positivos.
29. Como pesquisador, quero registrar custo e falhas, para publicar denominadores completos.
30. Como mantenedor, quero proteger a coleta, para preservar a evidência.
31. Como estudante, quero resolver casos inéditos, para demonstrar transferência do aprendizado.
32. Como estudante, quero documentar intervenções humanas, para justificar decisões críticas.
33. Como estudante, quero receber avaliação humana, para identificar lacunas e retestes.
34. Como autor, quero publicar estudos verificáveis, para construir portfólio.

## Implementation Decisions

O [estado da implementação](docs/implementation-status.md) descreve componentes, limites e próximos passos. O [guia de execução](docs/running-the-lab.md) explica como praticar.

| Decisão | Contrato |
| --- | --- |
| Ferramentas | Adotar o inventário documentado do PentAGI por etapas, com versões, disponibilidade e perfis verificados. |
| MCP red e blue | Preservar contratos e serviços internos; construir os servidores na próxima etapa. |
| Hipóteses | Usar busca em profundidade limitada, origem de evidência, deduplicação e fila de ramos pendentes. |
| Aprendizado | Exigir prática manual, assistida e inédita; registrar avaliação humana e lacunas. |
| Encerramento | Produzir documento final de aprendizado, supervisão e intervenção humana, vinculado aos episódios. |
| Tracker | Usar o Linear para capacitação e novos requisitos; manter links para as issues técnicas existentes no GitHub. |

O [inventário PentAGI](https://github.com/MathBorgess/red-blue-field/blob/main/docs/pentagi-tools.md) distingue ferramentas documentadas de ferramentas instaladas. O terminal pertence ao executor isolado da etapa local.

O [contrato MCP](https://github.com/MathBorgess/red-blue-field/blob/main/docs/mcp-red-blue.md) define operações, autorização e provas de conexão da próxima etapa.

A [busca por hipóteses](https://github.com/MathBorgess/red-blue-field/blob/main/docs/hypothesis-search.md) separa observação, inferência e achado. Uma categoria de risco orienta a investigação; sua presença exige teste.

Preservar S01–S18 e seus oráculos. Memória e autonomia pertencem ao núcleo; propagação em grafo lógico permanece opcional.

| Dimensão | Valores e interpretação |
| --- | --- |
| Ambiente | Replay, serviço local real, emulação cloud e cloud real; conclusões separadas. |
| Ator ofensivo | Manual, script, agente assistido e autonomia limitada. |
| Acesso | Black box, gray box e white box: informação externa, parcial e código autorizado. |
| Defesa | A: vulnerável; B: controles determinísticos; C: B com blue; D: C com revisão. |
| Ablação | Variar uma proteção interna por vez; manter contenção externa constante. |

A identidade de controle provisiona, emite escopo e encerra episódios. Red, alvo e blue operam com capacidades separadas.

O contrato fixa recursos, identidades, ações, destinos, prazo, orçamento e recuperação. Recursos descobertos permanecem candidatos até confirmação pelo controlador.

O broker conserva credenciais de modelo e cloud. Somente o coletor grava evidência canônica; participantes produzem artefatos candidatos.

Revisão humana vincula operação, parâmetros, identidade, versão, prazo e uso único. O executor consome a decisão junto ao efeito, com idempotência.

O blue recebe sinais próprios, sem respostas reservadas do avaliador. Contenção usa ações previstas e preserva evidências anteriores.

Manter agente próprio antes dos adaptadores CrewAI e PentAGI. Radar, AgentDojo e Agent-SafetyBench conservam seus critérios e resultados separados.

A etapa cloud usa conta sandbox, recursos exatos, sessões temporárias e política atual do provedor. Verificar custos, auditoria, restauração e remoção dos recursos.

Avaliar AgentCore quando necessário. A documentação consultada trata Bedrock Agents Classic como serviço fechado a novos clientes.

Cada episódio gera manifesto, escopo, eventos, efeitos e veredito. A revisão acrescenta hipóteses, histórico de intervenção e avaliação de aprendizagem.

## Testing Decisions

A fronteira principal continua o episódio completo. O avaliador verifica resposta, banco, processo e estado cloud, conforme o cenário.

Os testes dos servidores também verificarão o protocolo e a autorização. Anotações de ferramenta descrevem comportamento; o servidor decide a permissão.

| Critério de aceitação | Prova exigida |
| --- | --- |
| Fundação | Tarefa legítima e violação conhecida com efeito conferido no alvo. |
| Pentest local | Canary protegido e marcador inofensivo de execução, quando aplicável. |
| Ferramentas | Versão, parâmetros, destino, saída, término e comparação manual/agente. |
| Agente interno | Objetivo, ferramentas, memória e autonomia com controles benignos. |
| Cloud | Identidade efetiva, mudança observada, auditoria, restauração e teardown. |
| Cadeia híbrida | Evidência de cada transição serviço→agente→cloud. |
| Hipóteses | Ramo com três níveis, hipótese refutada, ciclo deduplicado e término por orçamento. |
| Escopo | Nova hipótese preserva recursos e ações autorizados; bloqueio externo tem rótulo próprio. |
| MCP red, etapa futura | Dois clientes compatíveis descobrem ferramentas e completam teste local auditável. |
| MCP blue, etapa futura | Dois clientes investigam sinal e executam contenção reversível auditável. |
| Separação de papéis | Identidade red falha ao chamar contenção blue; blue mantém suas permissões específicas. |
| Supervisão | Ação aceita, recusada, alterada e expirada; decisão humana antes do efeito. |
| Coleta | Falha suspende novas ações; efeito sem reconciliação permanece desconhecido. |
| Auditoria | Verificador distinto confirma ou rejeita alegações; cobertura pendente permanece visível. |
| Aprendizado | Casos inéditos, execução manual, explicação, correção e reteste avaliados por pessoa responsável. |
| Documento final | Evidências, intervenções, rubrica, lacunas e decisão humana por competência. |

Separar famílias de desenvolvimento e avaliação. Resetar memória entre famílias; preservar memória somente quando for a variável estudada.

Usar controles benignos, casos sem falha e tarefas impossíveis no escopo. Publicar falhas, recusas, custos e resultados desconhecidos.

O piloto S01–S04 continua exploratório. Lotes locais, cloud e híbridos terão tamanho e orçamento congelados antes da execução.

## Out of Scope

O contrato limita a atuação a sistemas próprios ou formalmente autorizados. A infraestrutura do provedor permanece fora do alvo.

O desenho padrão exclui dados pessoais reais, credenciais permanentes nos participantes, propagação externa, persistência maliciosa e testes volumétricos cloud.

O inventário registra categorias avançadas do PentAGI como referência. Sua inclusão documental preserva as etapas e permissões definidas para cada exercício.

O encerramento avaliará competências demonstradas. Formação em outras especialidades e experiência profissional exigirão prática adicional.

## Further Notes

Esta revisão mantém as sete seções da [to-spec](https://github.com/mattpocock/skills/blob/49dd158d1076134a641b33efb035946536778336/skills/engineering/to-spec/SKILL.md).

O [plano de aprendizagem](https://github.com/MathBorgess/red-blue-field/blob/main/docs/learning-assessment.md) define a avaliação. O [modelo do documento final](https://github.com/MathBorgess/red-blue-field/blob/main/docs/final-learning-report-template.md) permanece sem resultados medidos.

O [backlog no Linear](https://github.com/MathBorgess/red-blue-field/blob/main/docs/linear-backlog.md) registra tarefas e dependências. As issues históricas do GitHub conservam o contexto técnico anterior.

A especificação do produto está em 0.4. Os oito contratos de evidência anteriores permanecem em 0.2; o contrato de hipótese usa 0.3.

Os testes da aplicação verificam mecanismos e efeitos locais. Conexões MCP, cloud real e validação humana de competências pertencem às etapas seguintes.
