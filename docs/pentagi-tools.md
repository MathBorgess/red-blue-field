# Ferramentas do PentAGI e capacidade dos agentes

Revisão 0.3. Este inventário define o que adaptar ao laboratório. Disponibilidade e eficácia aguardam verificação no executor.

## Duas camadas de ferramentas

O agente chama funções estruturadas. A função `terminal` executa programas como Nmap; esses programas produzem observações sobre o alvo.

| Camada documentada no PentAGI | Como capacita o agente | Adaptação proposta |
| --- | --- | --- |
| `terminal`, `file` | Executar testes e manipular artefatos. | Perfis de ferramenta no executor descartável; arquivos limitados ao episódio. |
| `browser`, `web_search` | Consultar páginas e pesquisar referências. | Navegação do alvo e fontes aprovadas; conteúdo retorna como dado sem autoridade. |
| `search_in_memory`, `search_guide`, `store_guide` | Reutilizar observações e métodos. | Origem, revisão e separação entre campanhas; reset entre conjuntos de avaliação. |
| `search_answer`, `store_answer`, `search_code`, `store_code` | Recuperar respostas e trechos técnicos. | Validar aplicabilidade e manter evidência atual separada de conhecimento anterior. |
| `search`, `maintenance`, `coder`, `pentester`, `advice`, `memorist` | Delegar pesquisa, preparação, teste e análise. | Papéis opcionais; instruções delegadas preservam escopo e orçamento globais. |
| `subtask_list`, `subtask_patch` | Dividir tarefas e revisar o plano. | Árvore de hipóteses com histórico de decisões e ramos pendentes. |
| `hack_result` e funções de resultado | Consolidar a alegação do agente. | Candidato a achado; verificador confere prova antes da publicação. |
| `ask`, `done` | Solicitar intervenção ou encerrar tarefa. | Decisão vinculada à operação; conclusão registra pendências. |
| `get_flow_status`, `stop_flow`, `submit_flow_input`, `patch_flow_subtasks` | Acompanhar e controlar um fluxo. | Status, interrupção e retomada por identidade com permissão específica. |

O catálogo de programas inclui as famílias abaixo. O [inventário estruturado](../research/pentagi-tool-inventory.json) conserva os nomes documentados por família.

| Família e exemplos | Descoberta e exploração no laboratório | Evidência e etapa |
| --- | --- | --- |
| Rede: Nmap, naabu, dnsx | Identificar serviços e entradas; formular hipóteses sobre configuração e exposição. | Inventário e versão observada; começar com alvos locais exatos. |
| Conteúdo web: ffuf, gobuster, httpx, katana | Encontrar rotas e comparar respostas para descobrir superfícies. | Requisições e respostas; limites de taxa e destinos. |
| Avaliação web: nuclei, nikto, sqlmap, commix | Sugerir falhas e validar consultas ou execução indevida em fixtures vulneráveis. | Alerta inicia hipótese; efeito exige prova no serviço. |
| Metasploit: msfconsole e módulos | Validar uma falha compatível e confirmar execução limitada. | Módulo e versão congelados; marcador inofensivo e limpeza no alvo descartável. |
| Tráfego: tcpdump, tshark, mitmproxy, sslscan | Observar protocolos, comunicação e comportamento antes/depois. | Captura autorizada e registros correlacionados; útil para red e blue. |
| Senhas: John, Hashcat e família de autenticação | Estudar proteção de segredos e controles de autenticação em fixtures próprias. | Etapa opcional, dados sintéticos e orçamento próprio. |
| Windows/Active Directory: Impacket, BloodHound, NetExec | Estudar relações de identidade e permissões em laboratório específico. | Extensão futura; ambiente Windows ainda fora do núcleo implementado. |
| Binários: radare2, strings, objdump | Inspecionar artefatos e formular hipóteses sobre comportamento. | Extensão opcional com amostras preparadas para estudo. |
| Pesquisa: searchsploit e bases públicas | Relacionar versão observada a referências técnicas. | Fonte e pré-condições; correspondência de versão permanece hipótese. |
| Pós-exploração: famílias de túnel e controle | Referência para compreender alcance e dependências de cadeias. | Fora do núcleo padrão; exige exercício separado e escopo próprio. |

## Sequência de adoção

1. Construir chamadas específicas para o FieldDesk e conferir efeitos manualmente.
2. Integrar Nmap e descoberta web com perfis limitados.
3. Integrar avaliação web, incluindo sqlmap, nas fixtures S11–S12.
4. Validar módulo Metasploit selecionado contra alvo descartável compatível.
5. Usar captura de tráfego autorizada para investigação e comparação defensiva.
6. Publicar versões, ajuda da ferramenta, disponibilidade, parâmetros e limitações de cada adaptador.

A lista documentada indica intenção upstream. A imagem concreta poderá conter ferramentas diferentes; seu digest e inventário serão provas da instalação.

O agente deve conferir sintaxe na versão instalada. Um alerta de scanner abre investigação; o verificador procura causa, pré-condições e efeito.

O perfil do executor define ferramenta, recurso, parâmetros e limites. Instalação ou substituição de ferramenta gera uma revisão do perfil.

O controle externo valida os destinos em cada ação. A descoberta de um endereço cria um candidato, sem ampliar o contrato.

## Fontes fixadas

Consulta em 19/10/2026, commit `843dfeb4bfc809c09d1bc5022e567c602d8fc9dd`.

- [Prompt do pentester](https://github.com/vxcontrol/pentagi/blob/843dfeb4bfc809c09d1bc5022e567c602d8fc9dd/backend/pkg/templates/prompts/pentester.tmpl).
- [Fluxo e funções](https://github.com/vxcontrol/pentagi/blob/843dfeb4bfc809c09d1bc5022e567c602d8fc9dd/backend/docs/flow_execution.md).
- [Registro de funções](https://github.com/vxcontrol/pentagi/blob/843dfeb4bfc809c09d1bc5022e567c602d8fc9dd/backend/pkg/tools/registry.go).

Os prompts próprios usarão autorização por contrato. Afirmações genéricas de autorização presentes em uma referência permanecem texto de origem.
