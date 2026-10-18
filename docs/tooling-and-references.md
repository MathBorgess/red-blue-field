# Ferramentas e referências verificadas

Consulta em 18/10/2026. Adoção é proposta; nenhuma ferramenta externa foi instalada ou executada nesta revisão.

| Referência | Papel no projeto | Limite a conferir |
| --- | --- | --- |
| [PentAGI](https://github.com/vxcontrol/pentagi) | Referência de planejador, execução de ferramentas, memória e telemetria; adaptador comparativo opcional. | Fixar revisão, capacidades e exportação realmente disponível; a plataforma não substitui o nosso controlador de escopo. |
| [Cloudflare security-audit-skill](https://github.com/cloudflare/security-audit-skill) | Referência de auditoria white box, ledger de cobertura e verificação independente de achados. | Método de análise de código e validação local; não é autorização nem backend para testes cloud. |
| [CrewAI](https://github.com/crewAIInc/crewAI) | Adaptador para comparar orquestração com o agente simples. | Código aberto e ofertas comerciais são coisas distintas; modelo e infraestrutura podem ter custo. |
| [Agentic Radar](https://github.com/splx-ai/agentic-radar) | Inventário do workflow, ferramentas/MCP e testes em runtime suportados. | O README consultado diferencia scan de test; o suporte de runtime não é igual para todos os frameworks. |
| [AgentDojo](https://github.com/ethz-spylab/agentdojo) | Casos e protocolo de ataques/defesas por prompt injection em agentes com ferramentas. | Benchmark não cobre todo pentest de rede ou cloud. |
| [Agent-SafetyBench](https://github.com/thu-coai/Agent-SafetyBench) | Referência de segurança comportamental e avaliação em ambientes de agentes. | Escore do benchmark não é prova de resistência do serviço nem taxa de incidentes reais. |
| [CloudGoat](https://github.com/RhinoSecurityLabs/cloudgoat) | Referência de laboratórios cloud vulneráveis por desenho. | Rever IaC, permissões, custos e licença antes de adaptar; não importar credenciais do host para o worker. |
| [OWASP WSTG](https://owasp.org/www-project-web-security-testing-guide/) e [API Security 2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/) | Métodos e riscos da frente tradicional. | Fixar versão; não converter todo risco clássico em risco específico de IA. |
| [OWASP Agentic 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) e [GenAI/LLM 2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/) | Taxonomias complementares para comportamento, ferramentas e aplicações. | São listas distintas; o mapeamento de cenários é interpretação deste projeto. |
| [MITRE ATLAS](https://atlas.mitre.org/) | Organizar técnicas e relacionar casos. | Verificar evidência de cada caso e revisão da taxonomia; não inventar identificadores. |
| [AWS Agentic AI Security Scoping Matrix](https://aws.amazon.com/blogs/security/the-agentic-ai-security-scoping-matrix-a-framework-for-securing-autonomous-ai-systems/) | Distinguir agência/autonomia e selecionar controles da arquitetura. | Não equivale à matriz GenAI nem aos perfis A/B/C/D. |
| [AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html) | Candidato a runtime/integração gerenciada para casos permitidos. | Oferta, cobrança e política aplicável ao uso devem ser conferidas. |

## Decisões de integração

O [plano de construção a partir de PentAGI e Cloudflare](reference-blueprints.md) liga cada referência a módulos, artefatos e critérios de aceitação. A primeira implementação será pequena; a adoção integral de plataformas não é requisito.

Implementar uma interface comum para entradas, ferramentas e evidência antes de integrar frameworks. Comparar os mesmos casos e permissões; trocar de framework junto com modelo, contexto e ferramentas impede atribuir o efeito à orquestração.

Radar deve produzir um relatório de superfície e, quando suportado, um teste de runtime. A revisão consultada lista scan para vários frameworks e runtime test para OpenAI Agents; a existência de extras CrewAI não significa cobertura equivalente de runtime. Registrar capacidades usadas e indisponíveis, sem prometer uma integração inexistente.

AgentDojo e SafetyBench entram como conjuntos externos com seus próprios ambientes e critérios. Seus escores permanecem separados dos cenários FieldDesk, do pentest local e da medição cloud. Validar licenças antes de redistribuir dados.

A documentação da AWS consultada informa que [Bedrock Agents Classic](https://docs.aws.amazon.com/bedrock/latest/userguide/agents.html) está em manutenção e fechado a novos clientes, e aponta para AgentCore. Portanto, Classic não é dependência de entrada para um novo laboratório. O adaptador gerenciado será escolhido quando a etapa for implementada.

## Scoping da AWS

A matriz agentic descreve quatro escopos: No agency, Prescribed agency, Supervised agency e Full agency. Ela orienta a análise de arquitetura. Os modos manual, script e agente e os perfis de defesa do laboratório são dimensões experimentais próprias; não presumir correspondência um a um.

A matriz GenAI continua útil para responsabilidade e solução, mas não substitui a análise de agência e autonomia do sistema executável. Citar a fonte e a revisão usadas em cada threat model.
