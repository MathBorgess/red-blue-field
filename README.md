# red-blue-field

Laboratório de estudo de segurança com áreas para investigação, defesa e alvos. O trabalho com agentes usa o Codex local; o laboratório mantém cenários manuais e roteiros conhecidos para estudar efeitos e controles.

## Onde começar

- [RED](RED/README.md): investigação e testes dentro do escopo definido.
- [BLUE](BLUE/README.md): análise, correção, contenção e reteste.
- [FIELD](FIELD/README.md): aplicações e cenários de estudo, incluindo Northstar Tasks.
- [Guia do FieldDesk](docs/running-the-lab.md): instalação e execução dos cenários locais.
- [Estado da implementação](docs/implementation-status.md): componentes, limites e validação pendente.

`red_blue_field/` contém o núcleo compartilhado de controle, cenários e evidências. As pastas RED e BLUE organizam o trabalho por papel; não são fronteiras de segurança independentes. Defina o alvo, as ações permitidas e os limites de cada exercício antes de operar. Evidências e credenciais permanecem fora do repositório público.

## Dois ambientes de estudo

O **FieldDesk** é o laboratório Python existente, com dados sintéticos e cenários manuais ou roteirizados. O [guia de execução](docs/running-the-lab.md) explica como usá-lo. Roteiros conhecidos testam mecanismos do laboratório; não medem descoberta autônoma.

O **Northstar Tasks** é uma aplicação sintética incluída em [FIELD](FIELD/codex-security-client-app/README.md), distribuída para revisão estática. O teste de comportamento legítimo descrito no próprio aplicativo é limitado e não comprova o funcionamento completo da aplicação.

## Integrações e evidências

Há implementação de servidores MCP Red e Blue no núcleo. Sua conexão aos clientes e seu uso neste fluxo ainda precisam de validação; veja [MCP](docs/mcp-red-blue.md). A reorganização retira o fluxo próprio de chats e proxy: use o Codex local conforme a configuração do seu ambiente.

Registre hipótese, alternativas, evidência observada, limite da validação e resultado do reteste. Uma falha identificada por leitura é uma hipótese até que a evidência sustente a conclusão. O [vocabulário](GLOSSARY.md) e o [desenho experimental](docs/experiment-design.md) dão mais contexto.
