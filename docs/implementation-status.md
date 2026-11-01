# Estado da implementação

O repositório reúne trabalho de [RED](../RED/README.md), [BLUE](../BLUE/README.md) e [FIELD](../FIELD/README.md). O Codex local apoia as atividades; o fluxo anterior de chats próprios e proxy foi retirado.

| Componente | Estado e limite |
| --- | --- |
| Northstar Tasks | Fonte sintética para revisão estática em `FIELD/codex-security-client-app/`; sua licença e proveniência estão na pasta. |
| FieldDesk | Aplicação, cenários, controlador e evidências no núcleo Python compartilhado. Modos manual e roteiro fixo são mantidos. |
| SPIFFE/WIF + OPA no FieldDesk | Bancada opcional em `FIELD/spiffe-wif-lab/`; usa dados sintéticos sem alterar a API ou os contratos dos cenários existentes. Em 2026-11-01, a matriz local mostrou atestação permissiva, audiência incompleta e autorização fraca de tenant, seguidas dos controles SPIRE/JWKS/OPA. Com o Fixture vulnerável, OPA bloqueou leitura e inserção entre tenants; indisponibilidade do OPA retornou 503 sem efeito. Duas execuções reais adicionais do Agents SDK para inserção propuseram a ação autorizada, inclusive com nota adversarial. Alice continua sintética; esses resultados não medem a segurança geral do modelo ou da infraestrutura. |
| Ferramentas e defesa | Perfis e ações definidos pelo laboratório; a pasta RED ou BLUE não amplia suas permissões. |
| MCP Red e Blue | Código de servidores presente. Conexão ao Codex e funcionamento no fluxo reorganizado ainda não foram validados. |
| Formação | A competência depende de prática, explicação, evidência e revisão humana; testes automáticos não a demonstram. |

O núcleo reúne responsabilidades em `red_blue_field/`; avaliar o que ainda é necessário é um trabalho posterior. Testes de cenários conhecidos demonstram os comportamentos que exercitam, sujeitos ao resultado da execução efetiva. A validação desta reorganização deve ser registrada junto à mudança, sem presumir que provas anteriores se repetiram.

A [especificação histórica](../SPEC.md) e outros documentos de desenho registram versões anteriores. Para operação atual, comece pelo [guia de execução](running-the-lab.md) e confira os limites de cada alvo.
