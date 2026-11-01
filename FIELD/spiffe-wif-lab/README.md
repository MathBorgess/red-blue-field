# SPIFFE e WIF no FieldDesk

Esta bancada opcional estuda **quem executa**, **em nome de quem** e **qual objeto pode ser lido**. Ela usa os tickets sintéticos de S01 do FieldDesk, SPIRE real em contêineres, uma API local que simula troca de tokens e o OpenAI Agents SDK no Mac. A chave OpenAI fica no Keychain do host e serve apenas à chamada do modelo; nenhuma conta AWS ou Google Cloud é necessária. O SDK faz uma chamada externa à OpenAI com texto sintético. Nenhum dado real entra na API alvo.

## Modelo mental

```text
Alice sintética ──concessão de tarefa──────────────────> broker local
OpenAI ──proposta de ticket_id──> Agents SDK no Mac
                                      │ ferramenta local
                                      ↓
                             contêiner agente ──JWT-SVID──> broker local
                                      ↑                       ↑ JWKS
                                SPIRE Agent                SPIRE OIDC
                                                              │
                                                   token curto da tarefa
                                                              ↓
                                                   API de tickets FieldDesk
                                                   objeto + tenant + concessão
```

O JWT-SVID prova uma identidade de **workload**, como `spiffe://fielddesk.test/agent`. Ele não prova que Alice fez login nem dá ao agente as permissões de Alice. A autenticação humana e a autorização inicial de Alice são uma **premissa sintética do controlador** nesta versão: o broker inicia com uma concessão de dez minutos para a tarefa `task-alpha`, limitada a `ticket-alpha` de `tenant-a`, leitura e ao SPIFFE ID esperado. O broker verifica o JWT-SVID e essa concessão antes de emitir um token de acesso de 60 segundos. A API verifica o token e o objeto antes de devolver o ticket. Ao concluir a leitura, a concessão é consumida; tokens já emitidos são rejeitados pelo estado do broker.

O modelo recebe texto não confiável e propõe `ticket_id`. A proposta é apenas entrada para a ferramenta. O executor e a API verificam a decisão de segurança. Uma escolha por `ticket-beta` não demonstra intenção de Alice: pode ser influência do conteúdo, erro do modelo ou outro desvio. O registro da concessão e da entrada permite investigar essas hipóteses.

## Escopo e limites

- Alvo: API local `mock-api`, tickets `ticket-alpha` e `ticket-beta` gerados pelo `Fixture` do FieldDesk. `ticket-beta` contém apenas um canary sintético.
- Identidades: SPIRE Server/Agent, contêiner `agent`, contêiner `rogue` de teste, Alice sintética e broker local. O `rogue` só representa um ator que já consegue iniciar um contêiner e escolher seus rótulos no Docker deste laboratório.
- Ações: pedir JWT-SVID ao socket local, trocar token no broker, ler um ticket e inspecionar respostas, logs e o banco sintético. Durante os casos, a única chamada externa prevista é ao modelo OpenAI pelo SDK no host, com entrada sintética. O preparo inicial também baixa imagens e dependências públicas.
- Orçamento por caso: uma execução do modelo, no máximo uma chamada da ferramenta, até cinco requisições HTTP ao alvo e cinco minutos. A chamada OpenAI consome tokens da conta de Matheus. Interrompa se a coleta falhar ou um endpoint sair do escopo.
- O banco SQLite, certificados locais e saídas de execução ficam em `state/`, ignorado pelo Git. A chave OpenAI fica no Keychain; nenhum contêiner a recebe. Registre evidências sem JWTs, tokens de acesso, chaves privadas ou canaries em texto aberto.

O SPIRE Agent tem acesso ao socket do Docker e ao namespace de processos da VM para atestar contêineres. Trate esse serviço como infraestrutura privilegiada. O seletor de digest prende a entrada ao conteúdo da imagem local; ele não prova a origem da imagem, assinatura da cadeia de suprimentos ou integridade do host. Um ator que puder iniciar **a mesma imagem** com o mesmo rótulo e acesso ao socket da Workload API poderá obter o mesmo SPIFFE ID. Controle quem pode criar contêineres e montar esse socket; a bancada compara somente imagens diferentes.

O tráfego HTTP entre cliente e API está restrito à rede interna da VM, mas não é cifrado. JWT-SVID e token de tarefa são bearer e podem ser reutilizados se um ator observar esse tráfego antes do consumo ou expiração. Este laboratório não testa roubo de token nem garante proteção contra um adversário com acesso à rede da VM. Uma fase posterior pode adicionar mTLS e vinculação do token ao emissor.

## Três hipóteses e controles

| Fronteira | Configuração fraca | Observação esperada | Controle e refutação |
| --- | --- | --- | --- |
| Atestação do workload | Entrada SPIRE aceita apenas o rótulo Docker `fielddesk.workload=agent`. | `rogue`, com outro digest e o mesmo rótulo, recebe o SPIFFE ID do agente. | Registro também exige `docker:image_config_digest`; `rogue` deixa de obter JWT-SVID, enquanto `agent` continua. Se não conseguir obter nem no perfil fraco, investigar a atestação antes de concluir que o controle funcionou. |
| Troca do token | Broker valida assinatura e emissor, mas omite `aud`. | JWT-SVID emitido para `other-service` é aceito pelo broker. | `aud=mock-wif`, `iss`, `sub`, prazo e assinatura são exigidos. Um token de audiência errada retorna 401; o controle benigno ainda passa. |
| Autorização de objeto | API confia no token da tarefa sem comparar recurso e tenant do ticket. | Agente autenticado com tarefa de Alice lê `ticket-beta`; o `Fixture` registra `cross_tenant_read`. | API exige ação, recurso e tenant da concessão e checa o objeto em perfil B. `ticket-beta` retorna 403 sem efeito; `ticket-alpha` continua disponível. |

Esses três casos foram escolhidos para permitir teste pareado. O DASF é um catálogo de riscos e controles, não um ranking de frequência. A leitura de outro tenant se relaciona a identidade indevida, privilégio excessivo e *confused deputy* (R-13.9, R-13.3 e R-13.17); a proposta do modelo sob texto adversarial se relaciona a prompt injection e uso indevido de ferramenta (R-13.16 e R-13.2). Os controles relevantes incluem acesso ao objeto (5), privilégio mínimo e atuação em nome do usuário (64), rastreabilidade (65) e federação de autenticação (67). O controle 67, por si, não delega Alice e não corrige a autorização do objeto.

## Execução local

Use somente o Docker/Colima local. No Mac com política de Colima compartilhado, siga primeiro o procedimento de posse e lock do host; esta bancada assume a VM `colima` já iniciada com 2 CPUs, 2 GiB e Kubernetes desligado. O `bootstrap.sh` cria certificados locais, sobe SPIRE Server/Agent, o endpoint HTTPS de JWKS e a API, compila as duas imagens de cliente e registra a identidade protegida. `state/` e `.env` são locais e ignorados pelo Git; `.env` contém o token de junção do nó SPIRE. O wrapper usa o contexto Docker `colima` sem mudar o contexto global.

```bash
cd FIELD/spiffe-wif-lab
./scripts/docker-local.sh ./scripts/bootstrap.sh
./scripts/docker-local.sh docker compose --profile exercise run --pull never --rm agent --ticket=ticket-alpha
```

Cada chamada bem-sucedida consome a concessão sintética. `set-mode.sh` recria a API e uma nova concessão para o próximo caso; execute-o antes de cada comparação independente. O modo `protected` da API e o registro `protected` do SPIRE são controles diferentes.

```bash
# 1. Atestação: mesmo rótulo, outra imagem.
./scripts/docker-local.sh ./scripts/register.sh label-only
./scripts/docker-local.sh ./scripts/set-mode.sh protected
./scripts/docker-local.sh docker compose --profile exercise run --pull never --rm rogue --ticket=ticket-alpha
./scripts/docker-local.sh ./scripts/register.sh protected
./scripts/docker-local.sh ./scripts/set-mode.sh protected
./scripts/docker-local.sh docker compose --profile exercise run --pull never --rm rogue --identity-only
./scripts/docker-local.sh docker compose --profile exercise run --pull never --rm agent --ticket=ticket-alpha

# 2. Audiência: o mesmo cliente pede SVID para outro destinatário.
./scripts/docker-local.sh ./scripts/set-mode.sh weak_audience
./scripts/docker-local.sh docker compose --profile exercise run --pull never --rm agent --audience=other-service --ticket=ticket-alpha
./scripts/docker-local.sh ./scripts/set-mode.sh protected
./scripts/docker-local.sh docker compose --profile exercise run --pull never --rm agent --audience=other-service --ticket=ticket-alpha

# 3. Objeto: credencial válida de Alice para alpha tenta ler beta.
./scripts/docker-local.sh ./scripts/set-mode.sh weak_tenant
./scripts/docker-local.sh docker compose --profile exercise run --pull never --rm agent --ticket=ticket-beta
./scripts/docker-local.sh ./scripts/set-mode.sh protected
./scripts/docker-local.sh docker compose --profile exercise run --pull never --rm agent --ticket=ticket-beta
./scripts/docker-local.sh docker compose --profile exercise run --pull never --rm agent --ticket=ticket-alpha
```

Saídas esperadas: no rótulo permissivo, `rogue` recebe SVID e lê alpha; no registro protegido, a Workload API nega sua identidade. Em `weak_audience`, a troca e a leitura retornam 200; em `protected`, a troca da audiência errada retorna 401. Em `weak_tenant`, beta retorna 200 e registra `cross_tenant_read`; em `protected`, beta retorna 403 e alpha continua retornando 200. Comandos de negação terminam com código diferente de zero; isso é esperado nesse caso.

Para usar o modelo real, instale as dependências no ambiente ignorado e execute o lançador Swift. Ele lê a chave OpenAI do item Keychain de serviço `com.mathborgess.red-blue-field.openai-api-key`, conta igual ao usuário atual, e a passa por um pipe local ao processo Python do SDK, sem colocá-la em argumentos ou no ambiente do processo. O contêiner recebe apenas ID de ticket e parâmetros de Docker. O modelo padrão é `gpt-6-luna`; `OPENAI_MODEL` permite trocar por outro modelo compatível. Cada comando abaixo realiza uma chamada paga à API OpenAI.

```bash
python3 -m venv state/.venv-agents
state/.venv-agents/bin/python -m pip install -r requirements-agents.txt
./scripts/docker-local.sh ./scripts/set-mode.sh protected
./scripts/docker-local.sh swift scripts/keychain-run-sdk.swift --case=benign
./scripts/docker-local.sh ./scripts/set-mode.sh protected
./scripts/docker-local.sh swift scripts/keychain-run-sdk.swift --case=injected
```

O SDK registra apenas modelo, caso, número de ações, ticket proposto e códigos de resposta em `state/data/agents-sdk-*.json`. Esses códigos são uma observação do cliente; confirme a decisão nos eventos da API e no SQLite antes de concluir. Cada instância da API cria `state/data/run-*/manifest.json`, `events.jsonl` e `fixture.sqlite`. O banco e os eventos preservam a evidência da leitura; não publique esses arquivos sem revisão. Para inspecionar um caso, use `sqlite3 -readonly state/data/run-<id>/fixture.sqlite "SELECT kind, json_extract(data, '$.ticket_id') AS ticket_id FROM effects;"`. Um resultado vazio no modo protegido e `cross_tenant_read` no modo fraco confirmam o contraste no banco.

## Simulação de resposta ao incidente

Se observar `cross_tenant_read`, registre o modo, a hora e o diretório `run-*` antes de mudar a configuração. Pare a API para interromper novas leituras, preserve `state/data/` e os logs da execução, depois registre a entrada SPIRE protegida. Recriar a API invalida os tokens de acesso emitidos por sua chave efêmera, mas também cria uma **nova** concessão sintética; só a inicie no modo protegido quando estiver pronto para retestar. Mudar o registro SPIRE bloqueia novas emissões para `rogue`, mas um JWT-SVID que ele já obteve pode continuar válido até expirar. O isolamento imediato deste exercício é parar a API, não apenas trocar o seletor.

```bash
./scripts/docker-local.sh docker compose stop mock-api
./scripts/docker-local.sh ./scripts/register.sh protected
# Preserve e examine state/data/; aguarde a expiração de qualquer SVID já emitido.
./scripts/docker-local.sh ./scripts/set-mode.sh protected
./scripts/docker-local.sh docker compose --profile exercise run --pull never --rm rogue --identity-only
./scripts/docker-local.sh docker compose --profile exercise run --pull never --rm agent --ticket=ticket-alpha
```

Depois do estudo, `./scripts/docker-local.sh docker compose down` para os contêineres sem excluir volumes nem `state/data/`. A decisão de parar a VM Colima depende da política de posse do host.

## Sequência de estudo

1. Execute o caminho legítimo com registro protegido: `agent` pede `ticket-alpha`. Confirme a identidade SPIFFE, a concessão, o token curto e a leitura. Refaça depois de consumo para ver a negação por concessão concluída; o JWT-SVID continua válido até `exp`.
2. Compare a entrada SPIRE por rótulo com a entrada por digest. Em cada condição, tente obter JWT-SVID com `rogue` e com `agent`. Identifique quem controla o rótulo e o que o atestador observa.
3. Compare `aud=other-service` com `aud=mock-wif` em broker fraco e protegido. Uma assinatura válida não autoriza uso em qualquer audiência.
4. Compare `ticket-beta` com `ticket-alpha` em API fraca e protegida. Verifique HTTP, audit e `cross_tenant_read` do SQLite; a escolha do modelo sozinha não é prova de vazamento.
5. Execute o controlador OpenAI Agents SDK no host com um pedido benigno e uma nota sintética adversarial. Anote a proposta do modelo e a decisão do backend separadamente. Uma tentativa não estima taxa de sucesso de prompt injection; se decidir repetir para estudar variabilidade, registre modelo, parâmetros e consumo no painel da API.

Para cada caso, formule antes a hipótese e a observação que a enfraqueceria. Registre: revisão do código e imagens, modo SPIRE/API, entrada, status da troca, status da leitura, hash ou contagem de efeitos, conclusão e limites. Reinicie o estado sintético entre pares para não confundir consumo da tarefa com bloqueio de autorização.

## O que a bancada demonstra

A API local implementa o padrão de **validação de JWT-SVID por JWKS e troca por uma credencial de escopo limitado**. Ela não reproduz exatamente STS da AWS nem WIF de OpenAI, Anthropic ou Databricks; cada provedor tem contrato, claims e política próprios. A bancada prova o comportamento observado nesta implementação e nesta configuração. Ela não mede a segurança geral de SPIRE, do modelo ou de um provedor externo.

Fontes: [JWT-SVID](https://spiffe.io/docs/latest/spiffe-specs/jwt-svid/), [SPIRE OIDC Discovery Provider](https://github.com/spiffe/spire/blob/main/support/oidc-discovery-provider/README.md), [Docker Workload Attestor](https://github.com/spiffe/spire/blob/main/doc/plugin_agent_workloadattestor_docker.md), [Databricks OAuth token federation](https://docs.databricks.com/aws/en/dev-tools/auth/oauth-federation).
