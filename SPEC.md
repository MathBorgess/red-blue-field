# red-blue-field — especificação para revisão

Revisão: **0.1 · 18/10/2026**. Estado: **proposta de implementação e estudo**. Pesquisa concluída nesta revisão; aplicação e agentes ainda não implementados. A fronteira principal de teste foi proposta ao usuário e aguarda confirmação. Nenhuma escolha sugerida abaixo deve ser lida como resultado de experimento ou aprovação já recebida.

## Problem Statement

Queremos entender como agentes de IA podem participar de ataques e da defesa de sistemas inteligentes, e onde a supervisão humana precisa intervir. Relatos reais, demonstrações de pesquisadores e receios sobre autonomia costumam ser apresentados juntos, embora sustentem conclusões diferentes.

Precisamos transformar essas perguntas em um laboratório próprio, pequeno e observável. Cada tentativa deve permitir verificar quem propôs a ação, qual permissão estava disponível, o que o sistema executou, como a defesa reagiu e qual efeito permaneceu. Sem esse vínculo, um relato convincente de sucesso ou bloqueio pode não corresponder ao estado da aplicação.

## Solution

Criar o repositório público red-blue-field com uma aplicação transacional fictícia, um agente red team e um agente blue team. Um controlador externo aos agentes limitará recursos e escopo; um avaliador separado verificará efeitos e utilidade legítima. Todos os episódios produzirão dataset e traces, incluindo tentativas recusadas, interrompidas ou com resultado desconhecido.

Começar pelo FieldDesk: dois tenants, tickets, documentos, pedidos, reembolsos simulados e caixa de saída local. Seu assistente de produto é parte do alvo, separado do blue team. O MVP estudará autorização entre tenants, prompt injection, metadados de ferramentas e aprovação vinculada à ação.

Comparar aplicação vulnerável, controles determinísticos, controles com blue team e controles com revisão humana. O isolamento do laboratório permanece o mesmo em todos os grupos. O estudo mede segurança junto de utilidade, contenção, recuperação, custo e qualidade da evidência.

## User Stories

1. Como estudante, quero distinguir incidentes relatados, demonstrações e hipóteses, para interpretar corretamente a evidência disponível.
2. Como estudante, quero relacionar cada cenário a uma fonte e a uma pergunta, para compreender o mecanismo estudado.
3. Como estudante, quero acompanhar uma operação legítima até o efeito no sistema, para entender onde identidade, autorização e execução se encontram.
4. Como operador do laboratório, quero iniciar um cenário com estado conhecido, para comparar execuções equivalentes.
5. Como operador, quero aplicar orçamento e prazo fora dos agentes, para encerrar um episódio mesmo quando o modelo insiste em continuar.
6. Como operador, quero verificar o isolamento com um sentinela controlado, para testar o limite técnico antes do ensaio.
7. Como solicitante legítimo, quero acessar apenas os objetos permitidos ao meu tenant, para preservar o isolamento dos dados.
8. Como solicitante legítimo, quero concluir tarefas corretas mesmo com a defesa ativa, para que segurança e utilidade sejam avaliadas juntas.
9. Como red team, quero conhecer as superfícies e ações permitidas, para construir tentativas dentro do cenário.
10. Como red team, quero receber feedback limitado e registrar minhas tentativas, para estudar adaptação sem acesso aos oráculos reservados.
11. Como red team, quero variar a mesma intenção entre entrada direta, documento e metadado, para comparar superfícies de manipulação.
12. Como blue team, quero receber eventos com origem verificável, para investigar sem confundir texto hostil com autoridade.
13. Como blue team, quero inspecionar o contexto permitido do incidente, para decidir com base no que estaria disponível à defesa.
14. Como blue team, quero revogar sessões e suspender capacidades de teste dentro de limites explícitos, para conter o incidente com alcance controlado.
15. Como blue team, quero registrar hipóteses, ações e evidências de resposta, para que sua contribuição seja comparável ao controle determinístico.
16. Como revisor humano, quero ver a ação exata, o recurso, os parâmetros e o efeito previsto, para tomar uma decisão concreta.
17. Como revisor humano, quero que meu aceite expire e valha uma única vez, para impedir reutilização ou alteração posterior da ação.
18. Como executor, quero conferir e consumir a aprovação junto do efeito, para evitar uma corrida entre revisão e execução.
19. Como avaliador, quero conferir acesso, transação e publicação no estado do sistema, para não depender do relato de nenhum agente.
20. Como avaliador, quero identificar efeitos parciais, para não tratar uma recusa tardia como prevenção.
21. Como avaliador, quero separar falha do ataque de falha da infraestrutura, para não produzir uma taxa de defesa artificialmente alta.
22. Como pesquisador, quero correlacionar chamadas de modelo, ferramentas, política e efeitos, para reconstruir uma sequência completa.
23. Como pesquisador, quero registrar tokens, chamadas e espera humana, para comparar custo total e benefício observado.
24. Como pesquisador, quero separar revisor simulado de pessoa real, para não confundir teste de protocolo com estudo de julgamento humano.
25. Como pesquisador, quero separar desenvolvimento e avaliação por linhagem de ataque, para reduzir vazamento entre os conjuntos.
26. Como pesquisador, quero repetir os pares e declarar limites de determinismo, para avaliar variação sem prometer reprodução exata do modelo.
27. Como responsável pela recuperação, quero restaurar o serviço e registrar perdas residuais, para diferenciar reparo do banco de reversão de todo o dano.
28. Como mantenedor, quero impedir que participantes alterem coletor e avaliador, para preservar a independência das conclusões.
29. Como mantenedor, quero exportar somente dados sintéticos e artefatos transformados com proveniência, para compartilhar o estudo em um repositório público.
30. Como leitor externo, quero reconhecer exemplos ilustrativos e verificar checksums, para não confundir formatos de documentação com resultados medidos.
31. Como leitor externo, quero ver denominadores, falhas e limites da amostra, para julgar o alcance das conclusões.
32. Como responsável pelo estudo, quero revisar cada fatia com evidência e explicação do mecanismo, para decidir o próximo investimento com base em aprendizado.

## Implementation Decisions

**Confirmado pelo pedido:** repositório público com o nome red-blue-field; aplicação simulada; agentes red e blue; experimentos com dataset e traces dos dois lados; pesquisa de relatos e estratégias; avaliação do plano antes da implementação.

**Propostas para revisão:**

- Organizar os módulos por aplicação alvo, assistente de produto, red, blue, executor de política, controlador, coletor, revisão e avaliador. Cada módulo tem identidade e permissões próprias.
- Adotar um contrato principal de execução de episódio: recebe cenário, fixture, perfil e orçamento; devolve efeitos, artefatos e veredito terminal. O controlador é o único dono do ciclo de vida.
- Usar S01–S04 no MVP. Os demais cenários permanecem expansão, sem compromisso de implementação simultânea.
- Manter quatro perfis A/B/C/D. A comparação B/C isola o acréscimo do blue; C/D isola revisão. Registrar toda mudança de política e não adaptar a defesa com o conjunto reservado durante a medição final.
- Executar primeiro com adaptadores determinísticos. Adicionar modelos somente após comprovar coleta, isolamento e verificação de efeitos. Manter o mesmo modelo alvo entre perfis comparados.
- Começar com Python, serviço HTTP pequeno, banco local transacional, eventos JSONL e OpenTelemetry. Framework e provedor são substituíveis; versões serão fixadas quando escolhidas.
- Manter inferência remota em broker separado, com credencial fora dos workers. Oferecer ferramentas locais específicas, sem shell ou acesso genérico à internet no MVP.
- Aplicar autorização de identidade, tenant, objeto e ação no servidor. A política valida toda chamada e o fluxo entre origem e destino dos dados.
- Vincular revisão a identidade, ação, parâmetros, versão do recurso e política, prazo e uso único. Consumir a decisão atomicamente com o efeito e usar idempotência.
- Limitar respostas autônomas do blue a ações de contenção previstas. Mudanças de código ou política ficam entre rodadas e produzem nova revisão experimental.
- Separar telemetria confiável do conteúdo observado. O avaliador tem acesso aos oráculos; red e blue não recebem esse acesso.
- Exigir manifesto, eventos, estados e rótulos verificáveis. Falha de coleta interrompe novas ações; efeitos não reconciliados permanecem desconhecidos.
- Separar registros ilustrativos, replay de fixture e execução com modelo. Custos desconhecidos ficam nulos, e exemplos não entram nas métricas.
- Separar artefatos brutos e exportação pública. A exportação tem manifesto e hashes próprios, com revisão de dados e licenças antes de publicar.
- Propor piloto de 80 episódios adversariais e 80 controles benignos com revisor simulado, sujeito à revisão de tamanho e orçamento. Um estudo com pessoas será dimensionado separadamente.

## Testing Decisions

**Fronteira principal proposta:** executar um episódio completo e inspecionar os efeitos externos, o estado da aplicação e os artefatos de evidência. A confirmação dessa fronteira está pendente; a especificação continua em revisão.

Um bom teste demonstra uma propriedade externa: acesso de outro tenant não entrega dados; ação alterada não reutiliza aprovação; um efeito parcial continua no relatório; a tarefa permitida termina; orçamento encerra o episódio; coleta incompleta não vira defesa bem-sucedida. Não basta comparar texto do agente ou conferir que uma função interna foi chamada.

Os módulos de aplicação, gateway, política, controlador, coletor, agentes e avaliador serão exercitados juntos nessa fronteira. Testes menores ficarão restritos a propriedades críticas difíceis de provocar com precisão por fora: corrida no consumo de aprovação, idempotência, vínculo de versões, autenticação de origem e recuperação após falha.

Não há testes executáveis de uma aplicação existente para reaproveitar. O AgentDojo oferece referência externa para tarefas e objetivos adversariais; o CaMeL oferece referência de mediação por capacidades. Isso não torna o laboratório uma reprodução desses sistemas.

Casos de aceitação propostos:

1. Operação legítima conclui e gera uma cadeia verificável da entrada ao efeito.
2. Tentativa entre tenants tem sucesso confirmado no perfil intencionalmente vulnerável e falha antes do efeito quando o controle correspondente está ativo.
3. Instrução em documento ou ferramenta não concede nova permissão no perfil protegido; a saída do canary é verificada no sink e na resposta entregue.
4. Aprovação falsa, expirada, reutilizada ou com parâmetro alterado não produz transação. A aprovação correta produz um único efeito mesmo com retry concorrente.
5. Blue recebe apenas sua view e registra o sinal antes de qualquer alegação de prevenção. Bloqueios já feitos pela política são atribuídos à política.
6. Perda de coletor ou falha do modelo preserva registro terminal e suspende ações; resultado desconhecido permanece no denominador apropriado.
7. Tentativa fora do escopo é bloqueada no gateway e no isolamento; o ensaio usa somente sentinelas controlados.
8. Recuperação restaura estado/serviço e conserva no relatório exposições já efetivadas.
9. Exportação valida contratos, referências, sequência e checksums; dados privados e exemplos ilustrativos não entram no dataset medido.

## Out of Scope

Ataques a serviços de terceiros; dados de pessoas ou empresas reais; conectores com contas reais; pagamentos reais; malware ou autorreplicação de processos e pesos; execução arbitrária de código no MVP; treinamento, destilação e autopromoção de políticas; auditoria de organizações mencionadas nas fontes; afirmações de segurança universal.

O grafo de propagação da expansão é uma simulação de estados. O contexto de conversas privadas delimita perguntas, sem copiar falas, identidades ou dados para o repositório público.

## Further Notes

Esta revisão foi sintetizada com a skill [to-spec de Matt Pocock](https://github.com/mattpocock/skills/blob/49dd158d1076134a641b33efb035946536778336/skills/engineering/to-spec/SKILL.md), na revisão indicada pelo link. O formato da skill foi preservado; decisões ainda não tomadas foram identificadas como propostas.

A skill prevê publicar a spec no tracker e aplicar `ready-for-agent`. Em 18/10/2026, o usuário definiu explicitamente GitHub Issues no novo repositório como destino e autorizou publicar a pesquisa e as issues. A especificação continua proposta para avaliação; publicar o backlog não confirma a fronteira de testes nem inicia implementação. A classificação de prontidão deve refletir a revisão do plano.

O repositório público foi criado pelo usuário em 18/10/2026 e sua existência foi confirmada pelo GitHub conectado. Pesquisa, spec e backlog são publicados nesse repositório. A documentação conserva separadas a preparação dos artefatos, a publicação e a execução futura do estudo. A avaliação do plano está na [issue #2](https://github.com/MathBorgess/red-blue-field/issues/2).

Antes da primeira chamada de modelo, definir provedor, modelos, orçamento e tamanho do piloto. Antes de um estudo humano, delimitar participantes, decisões e medições. Até lá, o trabalho concreto desta revisão é pesquisa, cenário e contrato de avaliação, sem experimento executado.
