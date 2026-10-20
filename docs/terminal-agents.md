# Chats Red e Blue com Deep Agents

Os scripts abrem dois chats independentes, ligados ao mesmo episódio do Field. Eles usam a proxy local do Codex pelo protocolo Responses.

O código usa a biblioteca Deep Agents. Ela executa o ciclo entre mensagens, ferramentas, observações e resposta.

O [cliente de referência do Graph Engineering](https://github.com/MathBorgess/graph-engineering-lab/blob/4ffb59ad151d8f544a4920daf00be11c3faede20/proxy/client.py) usa esse protocolo. As instruções abaixo seguem essa revisão.

## Preparar os serviços

Mantenha o Field e sua proxy local em execução. A proxy deve aceitar `/v1/responses` na porta configurada.

Esta entrega usa a proxy existente. A autenticação com o Codex pertence ao ambiente que executa essa proxy.

O Field pode rodar com `rbf serve` ou Docker Compose. Para instalar as dependências dos chats:

```bash
pip install -e '.[chat,test]'
```

Escolha um identificador de modelo disponível na sua conta. Os scripts exigem esse valor para evitar uma escolha oculta.

Os exemplos usam `SEU_MODELO_CODEX` como marcador. Troque esse texto pelo identificador real.

## Terminal Red

Na raiz do repositório:

```bash
python scripts/red_teamer.py --model SEU_MODELO_CODEX --verbose
```

O script cria um episódio manual S01, perfil A, com prazo de uma hora. Ele mostra o identificador do episódio.

Se o Field usa Docker Compose, selecione o arquivo `.env` explicitamente:

```bash
python scripts/red_teamer.py --model SEU_MODELO_CODEX --control-token-file .env --verbose
```

O leitor extrai somente `RBF_CONTROL_TOKEN`. Ele trata esse arquivo como configuração e preserva o segredo fora das mensagens do modelo.

Você também pode definir `RBF_CONTROL_TOKEN` no ambiente. Para anexar um episódio existente, use `--run-id IDENTIFICADOR`.

## Terminal Blue

Abra outro terminal na mesma pasta. Use o identificador mostrado pelo Red:

```bash
python scripts/blue_teamer.py --model SEU_MODELO_CODEX --run-id IDENTIFICADOR --verbose
```

Acrescente `--control-token-file .env` quando o Field usa o token desse arquivo.

As conversas e memórias ficam separadas. Os agentes compartilham somente os efeitos e eventos do episódio configurado.

## Controlar cada ação

O modo inicial permite conversar, planejar e registrar hipóteses. A execução de testes e a contenção aguardam sua autorização.

| Comando | Efeito |
| --- | --- |
| `/allow` | Habilita ações somente para a próxima mensagem. |
| `/metrics` | Mostra as métricas acumuladas dessa sessão. |
| `/reset` | Cria outra memória de conversa; preserva logs e alvo. |
| `/help` | Mostra os comandos. |
| `/finish` | Conclui o episódio e gera o dataset do Field. Afeta ambos os terminais. |
| `/stop` | Interrompe o episódio. Afeta ambos os terminais. |
| `/quit` | Fecha o chat; preserva o episódio até seu prazo. |

Para permitir ações durante toda a sessão, acrescente `--allow-actions`. O controlador continua aplicando escopo, orçamento e prazo.

O chat Red registra a hipótese antes da execução. Cada chamada a `execute_next_test` executa um passo vinculado à hipótese proposta.

Se outra ação entrar na fila, o controlador bloqueia a execução. O operador pode revisar as hipóteses no painel.

O Blue precisa observar os eventos antes de citá-los numa contenção. Sua resposta usa uma lista fixa de capacidades.

Os chats recebem acesso ao controlador por funções específicas de cada papel. Eles compartilham o token administrativo no processo cliente.

Essa separação limita as ferramentas expostas ao modelo. Autenticação independente por papel no servidor permanece uma entrega futura.

## Ferramentas de cada agente

| Papel | Ferramentas do Field |
| --- | --- |
| Red | `lab_context`, `propose_test`, `execute_next_test`. |
| Blue | `lab_context`, `observe_events`, `contain`. |

Ambos recebem `write_todos` e ferramentas de arquivos virtuais. Esses arquivos pertencem à memória da conversa, separados do disco do host.

O código bloqueia execução de shell e delegação automática. As ferramentas do Field usam endereços e episódio fixos.

## Examinar prompts e planos

Os prompts editáveis ficam em:

- `red_blue_field/prompts/red_terminal.md`.
- `red_blue_field/prompts/blue_terminal.md`.

Use `--system-prompt CAMINHO` para comparar outra instrução. O log registra o texto e sua impressão criptográfica.

O plano aparece nas chamadas a `write_todos`. As hipóteses registram teste, alegação, refutação e vínculo com as evidências.

Os scripts chamam a proxy pelo protocolo Hypertext Transfer Protocol (HTTP). Eles dispensam processos `codex exec`, varreduras Git e hooks desse terminal.

O Deep Agents ainda oferece mecanismos próprios: instruções de ferramentas, plano, arquivos virtuais e resumo de contexto.

A configuração substitui o perfil comportamental específico do Codex na biblioteca. Os pedidos registrados mostram as instruções que chegam à proxy.

A proxy e o provedor podem aplicar suas próprias transformações. As observações do cliente cobrem a fronteira entre chat e proxy.

Os logs mostram decisões resumidas, planos e ações. O raciocínio privado do modelo fica omitido.

## Logs e métricas

Cada terminal cria uma pasta em `artifacts/private/chats/PAPEL/SESSAO`. O terminal mostra o caminho exato.

| Arquivo | Conteúdo |
| --- | --- |
| `session.json` | Papel, episódio, modelo, prompt, versões e limites. |
| `events.jsonl` | Conversa, pedidos, respostas, ferramentas e mudanças do plano. |
| `metrics.json` | Chamadas, tokens, cache informado, latência, erros e negativas locais. |
| `latest-request.json` | Últimas mensagens e schemas de ferramentas enviados à proxy. |
| `latest-response.json` | Última resposta da proxy, com conteúdo privado omitido. |

Para ler o último pedido:

```bash
python -m json.tool artifacts/private/chats/red/SESSAO/latest-request.json
```

`--verbose` mostra o fluxo no terminal. Os arquivos conservam os eventos completos, com sequência e cadeia de impressões criptográficas.

Credenciais conhecidas recebem proteção nos logs. O intermediário bloqueia um pedido que contenha o token de controle do Field.

Os eventos do chat usam `session_id` e `run_id`. As ações Blue também registram a sessão e as sequências observadas no Field.

As ações dos chats usam episódios `manual` no Field. As métricas do modelo ficam nos logs do chat, separadas do orçamento interno do Field.

Nos episódios manuais, o assistente interno do Field usa comportamento simulado. Os dois Deep Agents são os participantes externos.

Os limites de chamadas encerram novos pedidos quando atingidos. O limite de tokens considera o uso já informado pelo provedor.

O próximo pedido pode ultrapassar esse total. Se o provedor omitir uso, o log marca a lacuna e mantém o limite de chamadas.

Custos em dólares permanecem `null` quando a proxy omite esse dado. Tokens informados também podem diferir das cotas comerciais da assinatura.

## Experimentos separados

Os arquivos `experiments/red_terminal.json` e `experiments/blue_terminal.json` definem os dois roteiros de estudo. Você pode revisar suas instruções antes da execução.

Execute o Red:

```bash
python scripts/red_teamer.py --model SEU_MODELO_CODEX --experiment --allow-actions --verbose
```

Copie o identificador mostrado. Execute o Blue no mesmo episódio:

```bash
python scripts/blue_teamer.py --model SEU_MODELO_CODEX --run-id IDENTIFICADOR --experiment --allow-actions --verbose
```

O Red investiga autorização por objeto. O Blue examina os eventos e pode revogar a sessão após uma leitura indevida.

Abra o Red novamente com `--run-id IDENTIFICADOR` para conferir o bloqueio de outra tentativa. Revogar a sessão pode afetar consultas legítimas.

Uma saída indevida já observada continua no registro do incidente. Contenção limita novas ações; sua avaliação deve incluir essa perda residual.

Após conferir os dois fluxos, use `/finish` para gerar o resultado do episódio. Exporte seus artefatos pelo painel do Field.

Você pode trocar os roteiros com `--prompt "SUA MENSAGEM"`. O uso de `--experiment` conserva o episódio para a execução do outro papel.

## Estado da validação

Os testes usam Deep Agents, o cliente Responses e o Field reais, com respostas simuladas do provedor. Eles verificam ações, planos, papéis e logs.

O [registro de validação](../research/terminal-validation.json) documenta 178 testes aprovados, incluindo 13 testes dos chats.

A execução com sua conta Codex exige a proxy autenticada no seu ambiente. O teste simulado permanece separado dessa validação.

O laboratório mantém dados sintéticos e alvos locais. Ele dispensa Daybreak e usa apenas os acessos disponíveis no modelo escolhido.
