# Trilha de estudo e entregas

Plano proposto para sessões práticas. A duração e os modelos serão definidos depois do primeiro piloto; nenhum custo de API foi autorizado ou incorrido por esta documentação.

| Etapa | Pergunta de aprendizado | Exercício e evidência para encerrar |
| --- | --- | --- |
| 1. Fronteiras de confiança | Quem autentica, autoriza, executa e verifica? | Desenhar o FieldDesk e acompanhar uma operação legítima até o banco. Explicar a diferença entre intenção e permissão. |
| 2. Falha clássica | Como uma leitura de outro tenant acontece sem depender de IA? | S01 com requisições fixas, correção no servidor e trace de sucesso/falha. Conferir acesso indevido e tarefa legítima. |
| 3. Falha agêntica | Como dados recuperados passam a influenciar ações? | S02 e S03, primeiro com adaptadores de replay e depois com modelo. Identificar a fronteira atravessada usando eventos. |
| 4. Defesa e resposta | O que o blue acrescenta à política determinística? | Comparação B/C com os mesmos casos e orçamento; medir detecção, contenção e falso bloqueio. |
| 5. Supervisão humana | O revisor tem contexto e poder para impedir o efeito? | S04 com revisor simulado para testar o protocolo; ensaio humano posterior separado. Demonstrar invalidação de ação alterada após aprovação. |
| 6. Recuperação e custo | O que se restaura, o que permanece e quanto custa? | Incidente local com snapshots e sink; medir restauração do serviço e exposição residual. Somar defesa, retries e espera humana. |
| 7. Generalização | A defesa funciona em variantes novas? | Avaliação congelada em famílias reservadas, relatório por cenário e export sintético com data card. |

## Sequência de implementação a avaliar

1. Contratos, fixture e executor sem LLM: estado, cenários, coletor e oráculos.
2. Uma fatia completa de S01, da tentativa ao dataset, incluindo controle benigno e falha de coleta.
3. Broker/adaptadores de modelo e S02, preservando a mesma avaliação por efeitos.
4. Registro de ferramentas e S03; detector determinístico antes de adicionar o blue.
5. Blue separado, view limitada e respostas reversíveis; comparar B/C.
6. Revisão vinculada e S04; validar atomicidade, idempotência e versões.
7. Piloto, variantes reservadas, relatório e revisão dos cenários de expansão.

Cada fatia deve deixar um comando reproduzível, traces inspecionáveis e a explicação do mecanismo. Não encerrar por uma demonstração visual isolada ou por testes que apenas confirmem a implementação.

## Decisões para a revisão do plano

- Adequação do FieldDesk e dos quatro cenários iniciais.
- Uso de um único contrato de execução de episódio como fronteira principal dos testes.
- Provedor, modelo e orçamento total antes de chamadas reais.
- Primeira avaliação humana: quais decisões observar e como separar esse grupo do revisor simulado.
- Quando publicar os casos reservados e como renovar o conjunto para avaliações futuras.

Recomendação inicial: começar sem custo de modelo, validar uma fatia ponta a ponta e só então dimensionar a campanha com LLM. Treinamento, destilação e autoalteração dos agentes ficam para um estudo posterior, depois de existir uma régua estável.
