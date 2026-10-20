# Entrega executável 0.4

Esta entrega oferece um laboratório local para estudar segurança com agentes. Os contratos de evidência anteriores preservam suas versões.

## Componentes

| Componente | Estado da entrega |
| --- | --- |
| FieldDesk | Serviço HTTP, banco SQLite e dados isolados por episódio. |
| Controlador | Escopo, identidade, orçamento, prazo, interrupção e revisão vinculada. |
| Agentes | Roteiros fixos e adaptador opcional para modelos compatíveis com OpenAI. |
| Busca | Pilha em profundidade, hipóteses filhas, deduplicação e fronteira pendente. |
| Blue | Observação, quarentena, suspensão, revogação e restauração. |
| Cenários | S01–S18 executáveis; S10 usa grafo lógico. |
| Cloud | S13–S16 e S18 usam emulação local de permissões, rede e disponibilidade. |
| Execução no alvo | S12 usa contêiner descartável e marcador inofensivo. |
| Ferramentas | Oito perfis instalados; Metasploit informa indisponibilidade. |
| Painel | Experimentos, traces, hipóteses, decisões, campanhas, revisão e aprendizado. |
| Evidências | Manifesto, cadeia de eventos, artefatos, validação e exportação. |
| MCP red e blue | Contratos preservados. Servidores excluídos desta entrega, conforme o pedido. |

## Estrutura do código

| Arquivo | Responsabilidade |
| --- | --- |
| `red_blue_field/engine.py` | Serviços de aplicação e ciclo dos experimentos. |
| `red_blue_field/api.py` | Interface HTTP de controle e do alvo. |
| `red_blue_field/fielddesk.py` | Dados, falhas sintéticas e políticas do alvo. |
| `red_blue_field/tools.py` | Ferramentas permitidas e respostas blue. |
| `red_blue_field/agents.py` | Roteiros e chamadas ao modelo. |
| `red_blue_field/security.py` | Limites, escopo e decisões vinculadas. |
| `red_blue_field/evidence.py` | Coleta e validação de evidências. |
| `red_blue_field/utility.py` | Verificações específicas de tarefas legítimas. |
| `red_blue_field/worker.py` | Serviço descartável de execução e ferramentas. |
| `red_blue_field/static/` | Painel local, sem dependências externas de interface. |

O Model Context Protocol (MCP) conecta ferramentas aos agentes. Seus futuros adaptadores podem chamar os serviços de aplicação.

Eles deverão acrescentar autenticação própria, descoberta de ferramentas e testes de compatibilidade.

Uma conexão futura também deverá traduzir identidade e capacidades por papel. A interface de programação de aplicações (API) interna prepara parte dessa integração.

## Limites desta etapa

Os testes padrão usam roteiros conhecidos. Eles demonstram efeitos e controles nos serviços; alegações de robustez de modelos exigem execuções com modelos identificados.

Os testes do intermediário usam um provedor simulado. Eles verificam mensagens, orçamento, falhas e evidências, sem medir um modelo comercial.

A etapa atual dispensa licença Daybreak e acesso ampliado a modelos. Todos os componentes usam recursos comuns do ambiente local.

Os cenários cloud modificam estado do emulador local. Os resultados recebem o rótulo `cloud_emulated`.

Testes na Amazon Web Services (AWS) exigirão conta própria, escopo e configuração separados.

O FieldDesk compartilha o processo do controlador. Suas falhas controladas afetam dados sintéticos; execução de comandos ocorre somente no contêiner descartável.

O contêiner recebe comandos fixos de ferramenta. Alvos externos, argumentos livres e módulos arbitrários permanecem fora desses perfis.

O blue padrão aplica regras. Com modelo configurado, ele recebe observações autenticadas e escolhe respostas permitidas; o controlador valida cada resposta.

As comparações padrão usam informação parcial e casos conhecidos. Experimentos sobre descoberta inédita exigem famílias separadas e casos de avaliação reservados.

O parecer de aprendizado permanece pendente até a prática humana. Testes automáticos da aplicação comprovam comportamento do software, sem atribuir domínio ao estudante.

## Continuação do estudo

Siga o [guia de execução](running-the-lab.md) e registre os resultados por episódio. Use o [backlog de capacitação](linear-backlog.md) para organizar prática, explicação e reteste.

Os requisitos futuros de cloud real e conexão MCP permanecem documentados. Sua execução dependerá de ambiente próprio, configuração explícita e escopo correspondente.

## Pendências de implementação

1. Construir MCP red e blue, com autenticação por papel e testes com clientes compatíveis.
2. Oferecer os perfis da bancada também ao planejador do agente. Hoje, o operador aciona esses perfis pelo painel.
3. Ampliar os adaptadores do inventário PentAGI e verificar disponibilidade por imagem.
4. Automatizar a recriação dos alvos Docker entre episódios e após contenção. A restauração blue atual cobre o FieldDesk.
5. Acrescentar assinatura externa de evidências e identidades distintas para avaliadores humanos.
6. Criar infraestrutura e adaptadores para cloud real, com conta própria, custo limitado e descarte verificado.

## Chats externos com Codex

Os [scripts Red e Blue](terminal-agents.md) usam Deep Agents e o protocolo Responses da proxy local existente.

Cada chat registra prompt, plano, ferramentas, respostas e métricas em uma sessão própria. O identificador do episódio liga os dois fluxos.

Esses chats oferecem funções por papel sobre a interface local. Os servidores MCP permanecem na próxima etapa.

## Pendências de validação e estudo

1. Executar modelos identificados, dentro dos acessos disponíveis. Os testes atuais do intermediário usam um provedor simulado.
2. Reservar casos inéditos e comparar prática manual, roteiro e agente com repetições suficientes.
3. Medir falsos positivos, perda de utilidade e recuperação em campanhas com modelos.
4. Obter revisão humana externa e concluir o documento final de competências.

O relatório registra recuperação parcial quando restaura o FieldDesk e conserva marcadores no alvo Docker. Recriar os contêineres remove esses marcadores temporários.

## Verificação desta entrega

A execução local passou em 165 testes, incluindo navegador, contêineres, cenários, contratos e falhas. O [registro de validação](../research/validation-0.4.json) identifica os arquivos testados.

O teste completo com Docker Compose executou três serviços. S12 confirmou o marcador no perfil vulnerável, o bloqueio no protegido e a exportação de ambos.

Pacotes instalados sem metadados Git usam uma impressão do código no campo de revisão. `build.json` também conserva as impressões dos arquivos e versões das dependências.
