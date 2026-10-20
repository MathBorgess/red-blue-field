# MCP red e MCP blue

Revisão 0.3. Requisito de entrega ao fim dos experimentos; servidores e kit de desenvolvimento (SDK) ainda aguardam implementação.

Model Context Protocol (MCP) conecta ferramentas aos agentes. Ele padroniza a descoberta e a chamada de ferramentas por clientes de agentes.

O cliente continuará responsável pela decisão do agente. O servidor oferecerá operações e aplicará autorização, limites e registro de efeitos.

## Entregas de conexão

Entregar dois pacotes ou comandos instaláveis, com configuração de conexão e procedimento de teste. Cada servidor terá identidade e capacidades próprias.

Começar pelo transporte local `stdio`. Uma variante remota usará Streamable HTTP — transporte de chamadas pela rede — com autenticação, autorização e testes específicos.

Conferir a versão negociada do protocolo e fixar a versão do SDK. A referência de contrato é a especificação de 25/11/2025.

Validar descoberta e chamadas em dois clientes compatíveis. A entrega deve ensinar a conectar os servidores aos agentes do usuário.

## Ferramentas red propostas

| Nome | Entrada principal | Resultado e limite |
| --- | --- | --- |
| `red.get_scope` | Identificador do episódio. | Recursos, ações e prazo permitidos à identidade. |
| `red.discover_services` | Recurso e perfil de descoberta. | Inventário observado; adaptador Nmap limitado. |
| `red.test_web` | Hipótese, recurso e perfil web. | Requisições e artefatos; adaptadores específicos de descoberta e validação. |
| `red.validate_execution` | Hipótese e perfil de prova local. | Marcador inofensivo em alvo descartável; módulo permitido previamente. |
| `red.test_agent` | Caso, superfície e entrada sintética. | Desvio observado, chamadas propostas e efeitos. |
| `red.test_cloud_policy` | Recurso sandbox e caso permitido. | Permissão efetiva e mudança observada, quando autorizada. |
| `red.propose_hypothesis` | Pais, fonte, hipótese e refutação. | Nó candidato; controlador decide elegibilidade. |
| `red.get_evidence` | Referência de artefato do episódio. | Visão autorizada e origem verificável. |
| `red.get_run` | Identificador do episódio. | Operações, consumo, ramos e pendências visíveis ao red. |
| `red.stop_run` | Episódio próprio e motivo. | Cancelamento e estado reconciliado das operações próprias. |

Os adaptadores red usarão os [perfis do inventário PentAGI](pentagi-tools.md). A interface padrão oferece operações específicas por perfil.

O executor interno pode usar terminal. O contrato MCP público recebe recursos e parâmetros estruturados, com autorização no servidor.

## Ferramentas blue propostas

| Nome | Entrada principal | Resultado e limite |
| --- | --- | --- |
| `blue.get_scope` | Identificador do episódio. | Visão e capacidades defensivas permitidas. |
| `blue.query_events` | Janela, filtros e caso. | Sinais autenticados e conteúdo marcado pela origem. |
| `blue.inspect_state` | Recurso permitido. | Estado observável e integridade da coleta. |
| `blue.diff_configuration` | Recurso e versões. | Mudança em política, rede ou configuração do agente. |
| `blue.revoke_session` | Sessão de teste e motivo. | Revogação conferida no alvo. |
| `blue.quarantine_document` | Documento e versão. | Quarentena reversível e registro do impacto na tarefa. |
| `blue.suspend_tool` | Capacidade e sessão. | Suspensão limitada, com prazo e restauração. |
| `blue.isolate_workload` | Processo ou recurso do laboratório. | Contenção prevista no contrato; preservar o canal de coleta. |
| `blue.restore_configuration` | Snapshot e recurso. | Restauração com verificação de saúde e perdas residuais. |
| `blue.get_evidence` | Referência autorizada. | Evidência para investigação, sem oráculos reservados. |

A política do episódio define quais contenções podem ocorrer automaticamente. Ações de maior impacto exigem decisão humana vinculada à operação.

## Contrato comum por chamada

Cada operação com efeito inclui episódio, recurso, hipótese ou incidente, perfil, parâmetros e chave de idempotência. O servidor obtém a identidade pelo canal autenticado.

O servidor resolve o recurso dentro do escopo congelado. Entradas declaradas pelo modelo permanecem dados candidatos até essa validação.

O retorno inclui identificador da operação, estado, referências de evidência e decisão de política. Resultado de ferramenta e efeito no alvo permanecem campos distintos.

Operações longas retornam `operation_id` e estado consultável. Esse mecanismo é próprio da aplicação; suporte às Tasks do protocolo exige implementação e teste adicionais.

Usar `tools/list`, `tools/call`, `inputSchema`, `outputSchema` e `structuredContent`. Validar chamadas e respostas contra os contratos publicados.

Anotações como `readOnlyHint` descrevem intenção. O servidor continuará responsável pelo controle de acesso e pela verificação do efeito.

## Identidade, supervisão e evidência

| Propriedade | Implementação exigida |
| --- | --- |
| Separação de papéis | Identidades e permissões red/blue distintas, mesmo quando compartilham infraestrutura. |
| Credenciais | Broker conserva segredos; modelo recebe referências opacas e dados sintéticos. |
| Transporte local | Validar processo, diretórios, ambiente e permissões do sistema operacional. |
| Transporte remoto | Validar destinatário e escopos dos tokens; usar credenciais próprias para integrações posteriores. |
| Aprovação | Revisor externo ao agente; vincular ação, parâmetros, versão, prazo e uso único. |
| Cancelamento | Interromper processos e reconciliar efeitos mesmo após queda do cliente. |
| Coleta | Preservar eventos e artefatos fora da área gravável pelos participantes. |
| Catálogo | Fixar nomes, descrições, versões e hashes; mudança exige nova revisão de confiança. |

O blue poderá atuar sobre a sessão red de teste quando o contrato permitir. A identidade red continuará limitada às suas operações.

O controlador mantém uma interrupção independente dos servidores. Perda de coleta suspende novas ações e exige reconciliação dos efeitos possíveis.

## Aceitação

1. Instalar e conectar cada servidor em dois clientes compatíveis.
2. Descobrir ferramentas e completar chamadas com entradas e saídas válidas.
3. Rejeitar identidade, recurso ou parâmetro incompatível com o contrato.
4. Comprovar efeito red local e contenção blue reversível.
5. Conferir aprovação alterada, expirada e reutilizada antes do efeito.
6. Interromper operação longa e preservar o registro terminal.
7. Reconstruir a sequência com hipóteses, intervenções e provas.
8. Publicar configuração de exemplo, versões, limites e procedimento de recuperação.

Fontes: [ferramentas MCP](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) e [práticas de segurança](https://modelcontextprotocol.io/specification/2025-11-25/basic/security_best_practices).
