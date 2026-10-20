# red-blue-field — guia para agentes

Este repositório contém um laboratório local de segurança com dados sintéticos. Use o [guia inicial](README.md) como entrada para operadores humanos.

## Escopo e fontes

- Leia a [especificação](SPEC.md) e o [estado da implementação](docs/implementation-status.md) antes de alterar o comportamento dos experimentos.
- Mantenha ações nos recursos do episódio e nos alvos descartáveis do laboratório.
- Preserve limites de acesso do provedor. O projeto dispensa Daybreak.
- Preserve a separação entre roteiro fixo, modelo real, provedor simulado e emulação cloud.
- Registre hipóteses, critérios de refutação, observações e efeitos. Preserve o raciocínio privado do modelo.
- Guarde tokens e traces brutos em arquivos privados. Use [.env.example](.env.example) como contrato de configuração.
- Os servidores de integração red e blue pertencem à próxima etapa; os chats atuais usam a interface local.

## Preparar o ambiente

Execute na raiz do repositório:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[test,chat]'
test -f .env || .venv/bin/rbf init
docker compose up --build -d
```

Use `rbf init` somente quando `.env` estiver ausente. O comando cria tokens aleatórios e preserva arquivos existentes.

O operador configura `RBF_CODEX_MODEL` com um modelo disponível em sua conta. A proxy Codex deve aceitar `/v1/responses`.

Os chats leem `.env` sem executar shell ou expandir variáveis. A ordem de configuração é: argumentos, ambiente exportado, `.env`, padrões.

Para outra configuração, use `--env-file CAMINHO`. Para o Field em execução com `rbf serve`, selecione `--control-token-file artifacts/private/control-token`.

O token exportado em `RBF_CONTROL_TOKEN` prevalece sobre o arquivo de token selecionado.

## Abrir os chats

Terminal Red:

```bash
.venv/bin/python scripts/red_teamer.py --verbose
```

O Red cria um episódio manual S01, perfil A, mostra `RUN_ID=...` e grava `artifacts/private/active-run.json`.

Terminal Blue:

```bash
.venv/bin/python scripts/blue_teamer.py --verbose
```

O Blue usa esse arquivo e valida o episódio no servidor. As sessões mantêm memórias e logs separados.

## Identificar e selecionar o episódio

Leia o registro local:

```bash
.venv/bin/python -m json.tool artifacts/private/active-run.json
```

O campo `run_id` contém o identificador real. O campo `field_url` vincula esse identificador ao servidor.

O arquivo conserva uma seleção, sujeita à validação no servidor. Após um reinício ou encerramento, crie outro episódio quando necessário.

Para anexar um identificador explícito:

```bash
.venv/bin/python scripts/red_teamer.py --run-id IDENTIFICADOR --verbose
.venv/bin/python scripts/blue_teamer.py --run-id IDENTIFICADOR --verbose
```

Troque `IDENTIFICADOR` por um valor real. A prioridade é `--run-id`, `RBF_RUN_ID` e, para Blue, o arquivo `RBF_RUN_FILE`.

Com `RBF_RUN_ID` vazio, o Red cria outro episódio. Cada seleção Red atualiza o arquivo local.

Para experimentos simultâneos, passe `--run-file CAMINHO` aos dois terminais ou selecione os identificadores explicitamente.

## Execução e controle

Os chats começam com execução desabilitada. `/allow` habilita ações para uma mensagem; `--allow-actions` habilita ações na sessão.

O Red registra uma hipótese antes de executar um passo. Uma mudança na ação pendente bloqueia sua execução até nova revisão.

O Blue precisa observar os eventos antes de usá-los para justificar contenção. Suas ações ficam ligadas à sessão externa.

| Comando | Uso |
| --- | --- |
| `/metrics` | Conferir chamadas, tokens informados, latências e erros. |
| `/reset` | Criar outra memória de conversa, preservando alvo e logs. |
| `/finish` | Concluir o episódio e gerar seu resultado. Afeta ambos os terminais. |
| `/stop` | Interromper o episódio. Afeta ambos os terminais. |
| `/quit` | Fechar o chat, preservando o prazo do episódio. |

## Experimentos para automação

Execute os roteiros em sequência, no mesmo diretório de trabalho:

```bash
.venv/bin/python scripts/red_teamer.py --experiment --allow-actions --verbose
.venv/bin/python scripts/blue_teamer.py --experiment --allow-actions --verbose
```

O Red cria o episódio; o Blue usa o registro local. Os roteiros ficam em `experiments/red_terminal.json` e `experiments/blue_terminal.json`.

Também é possível enviar uma mensagem com `--prompt "MENSAGEM"`. Preserve escopo, seleção de episódio e autorização de ações da configuração escolhida.

## Evidências e validação

Os logs ficam em `artifacts/private/chats/PAPEL/SESSAO/`. Correlacione `session_id` e `run_id` com os eventos do Field.

Examine `session.json`, `events.jsonl`, `metrics.json`, `latest-request.json` e `latest-response.json`. Uso ausente e custo desconhecido permanecem explícitos.

Os episódios do Field usam o modo `manual`; as chamadas dos modelos ficam nos logs dos chats.

Para verificar mudanças nos chats e na configuração:

```bash
.venv/bin/python -m pytest -q tests/test_terminal.py tests/test_terminal_config.py
```

Para verificar o restante da aplicação:

```bash
.venv/bin/python -m pytest -q
```

Os testes de provedor usam respostas simuladas. Validação com uma conta Codex exige registrar uma execução real pela proxy configurada.

Consulte o [guia dos chats](docs/terminal-agents.md) para os detalhes. Ao alterar comandos ou configuração, atualize este guia, o guia inicial e `.env.example`.
