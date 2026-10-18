# Pesquisa: ataques, defesa e supervisão

Data de corte: **18/10/2026**. Escopo: fontes públicas primárias, demonstrações de pesquisadores, relatos de fornecedores e referências técnicas. Metadados e limitações de acesso estão em [sources.json](../research/sources.json).

As perguntas iniciais incluem segurança, supervisão, intervenção humana, proteção de dados e recuperação de ações indevidas. O contexto privado foi consultado para delimitar o estudo. Este documento usa fontes públicas e cenários genéricos; não atribui incidentes, falhas ou arquiteturas a participantes de conversas privadas.

## Casos e o que cada evidência permite afirmar

| Caso | Natureza da evidência | Mecanismo relevante | Inspiração para o laboratório |
| --- | --- | --- | --- |
| EchoLeak / CVE-2025-32711, divulgado em junho de 2025 | Vulnerabilidade demonstrada em produto de produção; isso não estabelece exploração disseminada contra clientes. | Conteúdo de email poderia influenciar o Copilot e provocar saída indevida de dados. | Documento sintético com instrução adversarial, canary e caixa de saída local; verificar o fluxo de dados. [Aim/Cato](https://www.catonetworks.com/blog/breaking-down-echoleak/), [registro Microsoft](https://msrc.microsoft.com/update-guide/vulnerability/CVE-2025-32711). |
| GitHub MCP, 26/05/2025 | Demonstração controlada da Invariant Labs. Não é evidência de invasão geral do GitHub. | Uma issue pública induziu um agente com acesso mais amplo a buscar conteúdo privado e publicá-lo. | Dados de dois tenants e ferramenta de publicação simulada; bloquear a passagem de uma origem privada para uma saída pública. [Pesquisa original](https://invariantlabs.ai/blog/mcp-github-vulnerability). |
| Tool poisoning, 01/04/2025 | Demonstração de uma classe de ataque em integrações com ferramentas. | Instruções hostis colocadas nas descrições que o modelo lê. | Registro local de ferramentas, alteração controlada de metadados e validação de versão e capacidades. [Pesquisa original](https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks). |
| Campanha detectada em setembro e divulgada em 13/11/2025 | Relato de investigação da Anthropic; atribuição e estimativas de autonomia vêm do fornecedor. | Uso de um sistema agêntico para encadear operações, com direção humana e erros do modelo. | Medir passos, tempo, intervenções e efeitos de uma campanha limitada; não importar percentuais de autonomia como expectativa do laboratório. [Relato original](https://www.anthropic.com/news/disrupting-AI-espionage). |
| Threat intelligence de setembro de 2026 | Relato do fornecedor sobre operações interrompidas entre dezembro de 2025 e agosto de 2026. Não é uma amostra de todo o mercado. | Agentes aparecem na execução e coordenação de operações; pessoas continuam definindo alvos e revisando etapas. | Distinguir automação observada, decisão humana e impacto confirmado; comparar eficiência em um alvo fictício fixo. [Relatório](https://www.anthropic.com/threat-intelligence-report-september-2026). |
| Incidentes em avaliações, análise de 09/09/2026 | Relato da Anthropic de quatro incidentes em avaliações com acesso indevido à internet por configuração incorreta; investigação independente anunciada na publicação. | O ambiente dizia ser uma simulação, mas permitia alcançar sistemas reais. | Testar escopo e interrupção em serviços falsos, verificando o bloqueio técnico antes de qualquer execução. [Análise e limitações](https://www.anthropic.com/research/alignment-assessment-cybersecurity-incidents). |
| Agentic Misalignment, junho de 2025 | Simulações deliberadamente construídas para provocar falhas; os resultados não estimam a frequência dessas condutas em produção. | Conflito entre objetivo, permissões e supervisão em situações fictícias. | Medir tentativa de burlar uma aprovação ou continuar após revogação, com um objetivo benigno e dados sintéticos. [Estudo](https://www.anthropic.com/research/agentic-misalignment). |
| Autorreplicação, 12/10/2026 | Experimentos controlados e projeções. O próprio desenho simplifica o acesso inicial e separa limitações de capacidade e tamanho do modelo. | Encadeamento de implantação e propagação em um conjunto de máquinas. | Simular propagação como transições em um grafo finito; medir alcance e contenção. Não tratar a projeção como relato de um worm autônomo circulando na internet. [Estudo](https://www.anthropic.com/research/self-replicating-ai). |

## Estratégias a estudar do lado red

São famílias de experimento no alvo local, com capacidades e orçamento descritos no cenário:

1. **Fronteira de autorização:** tentar ler ou alterar um objeto de outro tenant. Isso verifica uma falha clássica da aplicação, mesmo sem LLM.
2. **Desvio de tarefa por linguagem:** variar uma entrada direta e, depois, um documento ou ticket que o assistente recupera. Comparar a mesma intenção em superfícies diferentes.
3. **Composição de ferramentas:** tentar transformar uma leitura permitida em uma publicação indevida. O risco pode aparecer na sequência, mesmo quando cada ferramenta funciona como foi programada.
4. **Origem e persistência:** variar metadados de ferramentas e memórias simuladas, mantendo identificada a origem de cada conteúdo.
5. **Abuso da supervisão:** apresentar uma autorização falsa, reutilizar uma decisão antiga ou alterar os parâmetros depois da revisão.
6. **Pressão operacional:** criar ciclos limitados, solicitações repetidas ou instruções em evidências que o defensor lê. Medir o custo imposto à defesa e a preservação dos logs.

As combinações e hipóteses acima são propostas deste projeto. Não são reproduções integrais dos incidentes nem alegações de que cada sequência funcionará com um modelo atual.

## Estratégias a estudar do lado blue

| Camada | Controle proposto | Como avaliar |
| --- | --- | --- |
| Aplicação | Autorização no servidor por identidade, tenant, objeto e ação. | Comparar acesso legítimo e acesso entre tenants, com efeitos no banco como evidência. |
| Ferramentas | Menor privilégio, funções específicas e mediação de todas as chamadas. | Verificar se o bloqueio acontece antes do efeito e se a tarefa permitida continua funcionando. |
| Fluxo de dados | Rotular origem e destino; impedir saída incompatível com a classificação do dado. | Tentar transferir um canary interno para o sink público e conferir o ledger do sink. |
| Supervisão humana | Aprovar uma ação exata, com expiração, uso único e verificação no momento da execução. | Alterar parâmetros, versão do recurso e identidade após a revisão; medir aceites e recusas corretos. |
| Resposta | Revogar a sessão, colocar documento em quarentena, suspender uma ferramenta e restaurar estado de teste. | Medir tempo até contenção, dano acumulado e retorno da tarefa legítima. |
| Observabilidade | Coletor e avaliador separados dos agentes; logs de identidade, chamadas, política e efeitos. | Injetar falhas de coleta e tentativas de forjar eventos; verificar se a conclusão fica incompleta ou inválida. |

Essas escolhas se apoiam nas recomendações de [agência excessiva da OWASP](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) e em princípios de separação entre instrução confiável e dados não confiáveis. O [CaMeL](https://arxiv.org/abs/2503.18813v2) é uma referência de arquitetura para controle de fluxo e capacidades; a garantia descrita no artigo depende do modelo de ameaça e da implementação dele. Usar ideias semelhantes aqui não transfere essa garantia para o laboratório.

## Referências de avaliação

- [AgentDojo](https://arxiv.org/abs/2406.13352v3): referência para tarefas legítimas, objetivos adversariais e avaliação de ataques contra agentes que usam ferramentas. Inspirar o protocolo; não apresentar nosso conjunto como equivalente ao benchmark.
- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/): vocabulário para riscos de objetivos, ferramentas, identidade, supply chain, memória, comunicação, cascatas e confiança humana. Os mapeamentos do catálogo são interpretativos.
- [MITRE ATLAS](https://atlas.mitre.org/): taxonomia viva para organizar técnicas e mitigações. Fixar uma revisão antes de adicionar identificadores aos dados publicados.
- [OpenTelemetry para agentes](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md): referência para correlação de spans. As convenções GenAI consultadas estão em desenvolvimento; fixar a revisão usada na implementação.
- [CISA/NCSC: desenvolvimento seguro de IA](https://www.cisa.gov/news-events/alerts/2023/11/26/cisa-and-uk-ncsc-unveil-joint-guidelines-secure-ai-system-development): referência de ciclo de vida e operação segura.

## Conclusões de trabalho

O conjunto de fontes sustenta estudar duas direções: agentes como ferramentas de um atacante e agentes/aplicações como alvo. A segunda não se reduz a jailbreak: permissões, dados recuperados, ferramentas e saídas também definem o impacto.

Supervisão precisa produzir uma decisão aplicável e um registro verificável. Um texto dizendo “o humano aprovou” não prova autorização; uma mensagem dizendo “bloqueei” não prova contenção. O protocolo deverá conferir cada alegação no componente que executa o efeito.

O laboratório pode mostrar que um controle falhou ou funcionou nos cenários medidos. Não poderá demonstrar segurança universal, intenção interna do modelo ou ausência de risco fora do conjunto avaliado.
