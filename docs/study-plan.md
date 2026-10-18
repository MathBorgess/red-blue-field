# Trilha de aprendizado prático

O objetivo é dominar o mecanismo e demonstrar capacidade de avaliação. Cada módulo produz explicação própria, reprodução, prova do efeito, defesa e reteste. Um resultado negativo bem fundamentado também encerra um estudo.

| Módulo | Construir e estudar | Exercício e evidência |
| --- | --- | --- |
| 1. Agentes por dentro | Laço pequeno, ferramentas, identidade, memória, erro e interrupção. | Explicar e executar uma tarefa legítima do FieldDesk sem esconder o fluxo em framework. |
| 2. Segurança básica | HTTP, API, autenticação, autorização, banco e rede. | Desenhar fronteiras e reproduzir S01 manualmente com logs do alvo. |
| 3. Pentest com agente | Inventário, hipóteses, seleção de ferramenta e prova. | Comparar manual/script/agente em S11–S12; confirmar marcador no dado/processo e corrigir. |
| 3b. Auditoria e verificação | Código, cobertura, fronteiras e achados; método da Cloudflare. | Rastrear uma falha real, rejeitar um falso positivo e registrar uma validação bloqueada; corrigir e retestar. |
| 4. Objetivo e ferramentas | Prompt injection direto/indireto, composição e metadados. | S02–S03; separar desvio do modelo de efeito bloqueado pela aplicação. |
| 5. Memória e autonomia | Sessões, persistência, delegação, orçamento e revogação. | S05–S09; medir influência posterior, loops e resposta correta a tarefa impossível. |
| 6. Defesa e supervisão | Blue, origem de sinais, contenção e aprovação atômica. | B/C e C/D; S04; verificar proteção sem bloquear toda tarefa legítima. |
| 7. Frameworks e benchmarks | Adaptador CrewAI; Radar, AgentDojo e Agent-SafetyBench. | Comparar o mesmo caso com o agente simples e o framework; explicar a cobertura efetiva de cada ferramenta. |
| 8. Cloud security | IAM, rede, armazenamento, telemetria e infraestrutura como código. | S13–S15 em sandbox; comparar permissões pretendidas e efetivas, restaurar e verificar teardown. |
| 9. Cadeias híbridas | Falha de serviço altera agente; agente altera serviço/cloud. | S16–S18, com prova de cada transição e contenção blue. |
| 10. Método experimental | Ablação, pareamento, famílias reservadas e custo. | Publicar release por frente e ambiente, com falhas e denominadores. |
| 11. Portfólio | Relato técnico com artefatos auditáveis. | Produzir de cinco a dez estudos a partir de execuções; plano inicial com oito temas. |

A fase cloud começa depois de conta, recursos, política e orçamento definidos. O ambiente local permite aprender e produzir evidência antes desse investimento.

Construir o planejador/runner inspirado no [PentAGI](reference-blueprints.md) durante o módulo 3. Comparar a plataforma upstream somente depois de verificar a implementação própria. No módulo 3b, usar a skill da Cloudflare como referência de método, mantendo a verificação de código separada do pentest black box.

## Sequência de entregas

1. Fundação: escopo, fixture, coletor e primeiro episódio completo S01.
2. Duas frentes em paralelo lógico: agente red/alvo para S02 e pentest de serviço local para S11–S12.
3. S03, memória, autonomia, blue e revisão, com controles benignos.
4. Adaptador CrewAI e comparações de ferramentas; congelar o primeiro conjunto local reservado.
5. Campanha local e primeira release; preparar cloud sem pressupor equivalência da emulação.
6. S13–S15 cloud e S16–S18 híbridos; releases incrementais.
7. Estudos técnicos com links para runs, causas, correções e limitações.

A sequência é um plano de implementação; não é registro de execução nem agendamento.

## Como demonstrar domínio

Para cada módulo, o estudante deve conseguir:

- Explicar identidade, entrada, estado e fronteira atravessada.
- Distinguir a hipótese, o que observou e o que permanece desconhecido.
- Reproduzir a prova sem depender de uma narrativa do agente.
- Corrigir a causa, retestar e mostrar que a tarefa legítima continua funcionando.
- Explicar por que uma defesa falhou e qual outra camada conteve o efeito.
- Adaptar o experimento a uma variante nova sem alterar o oráculo para fazê-la passar.

A previsão de mercado apresentada é motivação para a trilha. As entregas medem competência e resultados do laboratório, não demanda futura por vagas.
