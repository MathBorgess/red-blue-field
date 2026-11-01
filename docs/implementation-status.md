# Estado da implementação

O repositório reúne trabalho de [RED](../RED/README.md), [BLUE](../BLUE/README.md) e [FIELD](../FIELD/README.md). O Codex local apoia as atividades; o fluxo anterior de chats próprios e proxy foi retirado.

| Componente | Estado e limite |
| --- | --- |
| Northstar Tasks | Fonte sintética para revisão estática em `FIELD/codex-security-client-app/`; sua licença e proveniência estão na pasta. |
| FieldDesk | Aplicação, cenários, controlador e evidências no núcleo Python compartilhado. Modos manual e roteiro fixo são mantidos. |
| SPIFFE/WIF no FieldDesk | Bancada opcional em `FIELD/spiffe-wif-lab/`; usa tickets sintéticos de S01 sem alterar a API ou os contratos existentes. Em 2026-11-01, a matriz local SPIRE/JWKS mostrou os três erros e seus controles: rótulo permissivo deu identidade ao contêiner `rogue`; audiência errada foi aceita apenas no modo fraco; leitura cruzada ocorreu apenas no modo fraco de tenant. Duas execuções reais do OpenAI Agents SDK propuseram `ticket-alpha` e foram autorizadas, inclusive uma com nota adversarial sintética. Isso valida esses casos observados, não a segurança geral do modelo ou do SPIRE. |
| Ferramentas e defesa | Perfis e ações definidos pelo laboratório; a pasta RED ou BLUE não amplia suas permissões. |
| MCP Red e Blue | Código de servidores presente. Conexão ao Codex e funcionamento no fluxo reorganizado ainda não foram validados. |
| Formação | A competência depende de prática, explicação, evidência e revisão humana; testes automáticos não a demonstram. |

O núcleo reúne responsabilidades em `red_blue_field/`; avaliar o que ainda é necessário é um trabalho posterior. Testes de cenários conhecidos demonstram os comportamentos que exercitam, sujeitos ao resultado da execução efetiva. A validação desta reorganização deve ser registrada junto à mudança, sem presumir que provas anteriores se repetiram.

A [especificação histórica](../SPEC.md) e outros documentos de desenho registram versões anteriores. Para operação atual, comece pelo [guia de execução](running-the-lab.md) e confira os limites de cada alvo.
