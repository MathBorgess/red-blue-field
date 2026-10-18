# red-blue-field — AI Pentest & Agentic Red Teaming Reference Lab

Revisão **0.2 · 18/10/2026**. Estado: plano de implementação e estudo. A direção desta revisão foi solicitada pelo usuário: usar agentes para pentest tradicional e cloud, alterar o comportamento do agente interno e estudar limites de guardrails e de capacidade ofensiva. Os componentes continuam não implementados.

## Problem Statement

Queremos aprender, com profundidade prática, como construir agentes e usá-los em avaliações de segurança. Precisamos tanto comprometer serviços e configurações deliberadamente vulneráveis do laboratório quanto manipular agentes que escolhem ferramentas, persistem memória e executam ações.

Um teste de prompt isolado não explica a passagem entre modelo, API, banco, IAM e rede. Um scanner executado por script também não demonstra que o agente descobriu a falha ou construiu uma cadeia. O projeto deve tornar observáveis essas diferenças e permitir comparar tentativas, defesas e recuperação.

O produto principal é compreensão demonstrável: reproduzir o mecanismo, explicar a causa, apresentar evidências, corrigir e testar novamente. Dataset, traces e estudos técnicos são parte de cada entrega.

## Solution

Transformar red-blue-field em um laboratório de referência com três frentes:

| Frente | Ator ofensivo e alvo | Resultado estudado |
| --- | --- | --- |
| Pentest com agentes | Pessoa, script ou agente red contra APIs, banco, execução local e configuração cloud próprios. | Descoberta, confirmação de falha, acesso e efeito efetivo nos serviços. |
| Agentic red teaming | Red contra o assistente interno, ferramentas, memória e fluxo de supervisão. | Desvio de objetivo, uso indevido de ferramentas, persistência da influência e autonomia excessiva. |
| Híbrida | Red encadeia uma falha de serviço com manipulação de agente ou uma ação cloud indevida. | Caminho completo, privilégio usado, efeito final, detecção e contenção. |

O FieldDesk será a aplicação fictícia central, com dois tenants, tickets, documentos, pedidos e operações administrativas. A arena incluirá serviços vulneráveis executáveis, banco sintético, worker descartável para provas de execução e recursos cloud efêmeros. O blue team será separado do assistente interno.

Progredir de replay para serviço local real, emulação cloud e cloud real. Comparar execução manual, script e agente com ferramentas e informação inicial equivalentes. Comparar também quatro perfis de defesa, mantendo a contenção externa constante.

## User Stories

1. Como estudante, quero construir um agente simples antes de atacá-lo, para compreender o laço entre objetivo, ferramentas e estado.
2. Como estudante, quero explicar identidade, agência e autonomia, para distinguir capacidade concedida de liberdade de decisão.
3. Como estudante, quero executar uma avaliação manual, para estabelecer uma referência compreensível.
4. Como estudante, quero repetir a tarefa com script e com agente, para medir o que a decisão do modelo acrescenta.
5. Como pentester, quero descobrir serviços dentro de um inventário autorizado, para levantar uma superfície verificável.
6. Como pentester, quero testar autenticação e autorização de APIs, para confirmar acesso indevido com evidência.
7. Como pentester, quero verificar uma falha de entrada que alcance o banco sintético, para entender seu efeito real.
8. Como pentester, quero provar execução em worker descartável por um marcador inofensivo, para distinguir execução confirmada de alegação.
9. Como pentester cloud, quero observar permissões efetivas de uma identidade de teste, para comparar intenção e capacidade.
10. Como pentester cloud, quero testar configurações de IAM, armazenamento e rede do laboratório, para identificar excesso de privilégio e exposição interna.
11. Como operador, quero observar a indisponibilidade controlada de um serviço e sua recuperação, para medir integridade e disponibilidade.
12. Como red team, quero induzir desvio observável de tarefa no agente interno, para medir goal hijacking.
13. Como red team, quero variar instruções diretas, documentos e metadados, para comparar superfícies.
14. Como red team, quero manipular uma memória entre sessões controladas, para estudar persistência da influência.
15. Como red team, quero observar loops e crescimento de ações, para testar limites de autonomia e orçamento.
16. Como red team, quero testar uma API de configuração do agente, para estudar o vínculo entre segurança do serviço e comportamento.
17. Como red team, quero encadear serviço, agente e cloud, para verificar cada fronteira atravessada.
18. Como red team, quero receber apenas o feedback permitido, para evitar vantagem indevida de informação.
19. Como pesquisador, quero identificar tentativas que apenas repetem um roteiro conhecido, para não atribuir descoberta ao modelo.
20. Como pesquisador, quero testar variantes reservadas e casos sem solução no escopo, para medir generalização e honestidade do relatório.
21. Como blue team, quero receber sinais autenticados do alvo e das ferramentas, para investigar com proveniência.
22. Como blue team, quero conter sessão, processo, documento ou capacidade de teste, para limitar o efeito observado.
23. Como blue team, quero detectar alterações de IAM e rede, para comparar configuração antes e depois.
24. Como blue team, quero preservar o registro de um efeito parcial, para não encobrir dano durante recuperação.
25. Como revisor humano, quero analisar a operação exata e seu contexto, para decidir antes do efeito.
26. Como revisor humano, quero que alteração de parâmetros invalide meu aceite, para impedir reaproveitamento.
27. Como operador, quero congelar escopo, recursos e permissões, para executar um episódio limitado.
28. Como operador, quero uma interrupção fora dos agentes, para encerrar tentativas persistentes.
29. Como operador, quero preparar e destruir recursos cloud por um controlador separado, para preservar a fronteira externa.
30. Como operador, quero verificar os limites do provedor e estimar custos, para planejar uma execução real.
31. Como avaliador, quero conferir resposta, processo, banco e estado cloud, para distinguir alegação de efeito.
32. Como avaliador, quero separar desvio de comportamento, compromisso de serviço e drift de configuração, para produzir rótulos úteis.
33. Como avaliador, quero identificar a camada de bloqueio, para estudar os limites de cada controle.
34. Como pesquisador, quero realizar ablações de guardrails, para evitar atribuir proteção à camada errada.
35. Como pesquisador, quero comparar eficácia com orçamento equivalente, para estudar limites do ataque com agentes.
36. Como pesquisador, quero registrar falhas, recusas, consumo e intervenção, para calcular denominadores e custo completo.
37. Como pesquisador, quero diferenciar emulação de cloud e serviço real, para limitar as conclusões.
38. Como estudante, quero comparar um agente simples com um adaptador de framework, para aprender sem esconder mecanismos.
39. Como estudante, quero usar Agentic Radar, AgentDojo e Agent-SafetyBench em seus papéis específicos, para avaliar cobertura e limitações.
40. Como mantenedor, quero proteger coletor, escopo e avaliador, para manter a independência da evidência.
41. Como leitor, quero reproduzir uma falha e a correção em laboratório, para verificar o estudo.
42. Como autor, quero produzir de cinco a dez estudos com artefatos reais, para construir portfólio verificável.
43. Como autor, quero preservar resultados negativos e limites, para comunicar descobertas com precisão.
44. Como responsável pelo projeto, quero encerrar cada módulo com explicação, prova, correção e reteste, para demonstrar aprendizado.
45. Como estudante, quero construir planejamento, execução e memória observáveis inspirados no PentAGI, para explicar decisões e comparar capacidade ofensiva.
46. Como auditor, quero inventariar código e cobertura e validar achados independentemente, para separar suspeita, prova e falso positivo.
47. Como pesquisador, quero comparar black box, gray box e white box, para medir o efeito da informação disponível.

## Implementation Decisions

**Direção confirmada:** repositório público; aplicação própria; agentes red e blue; pentest de serviços e cloud; manipulação do agente interno; estudo de guardrails, capacidade ofensiva e defesa; dataset e traces de todos os episódios. Esta revisão altera o plano, sem iniciar pentest ou provisionamento.

**Desenho proposto:**

- Separar plano de controle, arena alvo, workers ofensivos, assistência interna, blue, broker, coletor e avaliador. O red não administra a infraestrutura externa que o contém.
- Manter o FieldDesk e acrescentar API/banco vulneráveis, serviço de prova de execução e adaptadores de recursos cloud. A falha do alvo pode produzir um efeito real dentro do laboratório.
- Usar quatro ambientes explícitos: replay local, serviço local real, emulação cloud e cloud real. Emulação não valida semântica ou permissões da AWS.
- Usar três modos ofensivos: manual, script e agente; no agente, distinguir assistência de autonomia limitada. Ferramentas, informação inicial e orçamento devem ser comparáveis.
- Preservar S01–S10 e acrescentar S11–S18 para banco, execução local, IAM/armazenamento, rede, disponibilidade e cadeias híbridas. Memória e autonomia entram no currículo principal após a fundação; propagação em grafo permanece estudo opcional.
- Congelar um contrato de escopo com recursos, identidades, ações, destinos, prazo, limites e recuperação. Só a identidade de controle emite ou substitui esse contrato.
- Permitir shell e ferramentas de pentest apenas no worker específico de VM/microVM da etapa correspondente. O serviço alvo e o executor não recebem shell do host, diretório pessoal ou credencial de administração do laboratório.
- Manter separado o controle sob teste e o limite externo. Uma política intencionalmente fraca pode ser atacada; coletor, avaliador e recursos fora do episódio permanecem protegidos.
- Comparar perfis A/B/C/D para defesa e uma dimensão independente de ablação para prompt, filtro do modelo, política de ferramentas, autorização do serviço e composição.
- Separar desvio comportamental, ferramenta proposta, ferramenta executada, acesso confirmado, execução comprovada, mudança de configuração, indisponibilidade e restauração. Uma recusa do modelo não demonstra resistência do serviço.
- Criar primeiro um agente pequeno e transparente, depois um adaptador CrewAI. Avaliar AgentCore como integração gerenciada após os experimentos locais; não pressupor disponibilidade ou gratuidade de serviços gerenciados.
- Usar Radar para inventário/análise e testes suportados; AgentDojo para prompt injection; Agent-SafetyBench para avaliação de segurança comportamental. Cada integração congela revisão, licença e capacidades efetivamente usadas.
- Preparar recursos cloud em conta sandbox separada, com região e IDs exatos, sessões temporárias e permissões verificadas por ação. Controles de escopo não dependerão somente de nomes ou tags.
- Registrar trilha de ferramentas e auditoria de aplicação, banco, processo e cloud. Eventos de dados e logs de banco serão configurados quando necessários; não presumir que logs administrativos cubram todos os acessos.
- Fazer restauração e teardown pelo controlador, conservando drift e dano residual no relatório. Alertas de orçamento cloud não são tratados como teto absoluto de faturamento.
- Produzir releases incrementais por frente e ambiente, com casos reservados por linhagem. O piloto de quatro cenários continua uma calibração da frente agêntica, não cobertura de todo o projeto.
- Planejar oito estudos técnicos; cada um exige um episódio medido, evidência, causa, defesa, reteste e limitações. A publicação em redes externas depende de pedido específico.
- Usar [PentAGI e Cloudflare security-audit-skill como referências de construção](https://github.com/MathBorgess/red-blue-field/blob/main/docs/reference-blueprints.md): planejador/runner/memória/telemetria para pentest; cobertura, rastreio de código e verificador independente para auditoria. A integração comparativa do PentAGI é opcional e posterior ao runner próprio.
- Versionar `coverage-ledger.json` e `findings.jsonl` com o contexto de acesso e a revisão auditada. Achado confirmado exige prova; suspeita sem verificação permanece no ledger. `needs_validation` exige verificação independente e condição decisiva pendente; não recebe severidade.

## Testing Decisions

A fronteira principal é o **episódio completo**: escopo, tarefa, estado inicial, modo ofensivo, perfil e orçamento resultam em efeitos observados, evidência e veredito. Essa interface continua proposta para revisão; não é condição para concluir esta atualização documental.

Um bom teste verifica comportamento externo e estado: acesso entre tenants, canary no banco, marcador de execução na VM alvo, operação IAM realmente efetiva, regra de rede alterada e alcance observado, memória influenciando a tarefa seguinte ou serviço recuperado. Capturas de tela e relatos do modelo complementam a prova, sem defini-la.

Testes menores cobrem propriedades críticas: consumo atômico de aprovação, idempotência, resolução de escopo, revalidação de destinos, interrupção, autenticidade de eventos e coleta incompleta. As fontes de referência são WSTG/API Security, AgentDojo e os oráculos do próprio laboratório; não há aplicação existente já testada para reaproveitar.

Critérios de aceitação:

1. Uma tarefa legítima e uma violação conhecida são reproduzíveis, com o efeito conferido no alvo.
2. Pentest local confirma ao menos acesso a dado protegido e, na etapa de execução, um marcador inofensivo no worker alvo; um roteiro fixo não é apresentado como descoberta autônoma.
3. Pentest cloud selecionado demonstra permissões e mudanças nos recursos do sandbox, com auditoria, restauração e teardown verificados.
4. Desvio de objetivo, tool misuse, memória contaminada e loops têm cenário positivo, controle benigno e evidência do mecanismo.
5. Uma cadeia híbrida registra cada transição serviço→agente→cloud e a identidade usada.
6. Uma ablação altera um controle de cada vez e informa se a contenção externa impediu observar a falha do controle interno.
7. B/C identifica a contribuição adicional do blue; C/D mede revisão de uma operação exata.
8. Manual/script/agente compartilham o escopo e declaram diferenças de informação e ferramentas.
9. Recusa, falha de ferramenta, erro de infraestrutura e limite de orçamento têm classificações distintas.
10. O red e o alvo não alteram escopo, coletor ou oráculo; tentativa fora do contrato termina no controle externo.
11. Recuperação restaura o serviço e mantém exposições e perdas residuais registradas.
12. Exportação valida contratos, referências, checksums e redação; dados ilustrativos, emulação e cloud real permanecem distinguíveis.
13. Cada módulo deixa uma explicação do mecanismo, uma correção, um reteste e uma pergunta em aberto.
14. O portfólio contém apenas estudos apoiados em execuções e deixa explícito o que não foi demonstrado.
15. Uma auditoria white box discrimina achado confirmado, rejeitado e condição pendente, com cobertura incompleta visível e verificador distinto do descobridor.
16. O planejador liga objetivo, hipótese, ações e observações; uma comparação com PentAGI explicita diferenças de ferramentas, acesso e exportação, sem converter uma narrativa em prova.

## Out of Scope

Produção ou recursos de terceiros sem autorização; ataque à infraestrutura do provedor; dados pessoais reais; credenciais permanentes nos participantes; propagação autônoma fora do laboratório; malware persistente; testes volumétricos e DoS em cloud no desenho padrão; alteração do controle externo pelos agentes.

Provas de execução e ações destrutivas limitadas pertencem às etapas locais/recursos efêmeros definidos no contrato. A indisponibilidade em cloud será estudada por falha de configuração ou injeção controlada de falha compatível com o provedor. Treinamento e autopromoção de políticas ficam para estudo posterior.

## Further Notes

Esta revisão mantém o formato da skill [to-spec](https://github.com/mattpocock/skills/blob/49dd158d1076134a641b33efb035946536778336/skills/engineering/to-spec/SKILL.md). A discussão está na [issue #2](https://github.com/MathBorgess/red-blue-field/issues/2). Publicar o plano e o backlog não inicia os experimentos.

A matriz AWS para agentes distingue agência e autonomia; seus quatro escopos não equivalem aos perfis A/B/C/D deste projeto. A seleção de framework e serviço usará documentação atual. Bedrock Agents Classic é referência histórica para novos projetos; verificar AgentCore na etapa gerenciada.

A motivação de carreira fornecida pelo usuário orienta as competências. A previsão de demanda entre 2026 e 2030 não foi validada como estatística nesta pesquisa, e não será tratada como resultado do laboratório.

Conta cloud, recursos concretos, orçamento e regras aplicáveis serão definidos na preparação da etapa correspondente. Esta revisão não executou ataques, não provisionou serviços e não incorreu em custos de modelo do experimento.
