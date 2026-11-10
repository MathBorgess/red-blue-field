# MCP Red e Blue

O núcleo contém servidores MCP para os papéis Red e Blue, com transportes locais `stdio` e HTTP. A existência do código e seus testes anteriores não comprovam uma conexão funcional ao Codex nesta reorganização.

Antes de usar uma integração, valide separadamente descoberta e chamadas em um cliente, identidade e autorização de cada papel, escopo do episódio, tratamento de erros e efeitos observados. Registre versões, configuração e lacunas. As capacidades disponíveis são as implementadas no servidor e sujeitas ao controle do laboratório.

A conexão do Codex local ao MCP permanece pendente de validação. Para o uso atual do FieldDesk, consulte o [guia de execução](running-the-lab.md). O histórico Git preserva o contrato proposto na revisão 0.3.

## Laboratório remoto

O bridge `rbf-mcp-remote` encaminha stdio para o endpoint remoto do FieldDesk, mantendo a sessão de usuário Access e o token de papel separados. Ele não instancia outro `Lab`. O driver de alvo S02 é outro processo e recebe uma credencial target, sem a credencial de controle do pesquisador. Veja [preparação e limites do S02](s02-real-target.md).

A descoberta em teste de protocolo não comprova o carregamento no Codex Desktop. Registrar o servidor exige conferir comando, origem HTTPS, papel, episódio e arquivos de credenciais antes de habilitá-lo.
