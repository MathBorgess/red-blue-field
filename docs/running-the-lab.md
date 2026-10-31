# Executar o Field

Esta entrega funciona com Python 3.12 e Docker Compose. Os exercícios locais usam dados sintéticos e dispensam acesso ampliado a modelos.

## Início com Docker

```bash
git clone https://github.com/MathBorgess/red-blue-field.git
cd red-blue-field
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
rbf init
docker compose up --build -d
```

Abra `http://127.0.0.1:8080`. Use o valor de `RBF_CONTROL_TOKEN` criado no arquivo `.env`.

O painel exibe cenários, estado, hipóteses, eventos, revisões, ferramentas e aprendizado. Os tokens permanecem na memória da página.

O aplicativo recebe conexões pela interface local. Os alvos Docker usam rede interna, usuário sem privilégios e sistema de arquivos protegido.

As pastas temporárias recebem limites próprios. O aplicativo conserva evidências no volume `lab-data`.

Para encerrar os serviços:

```bash
docker compose down
```

O volume conserva os experimentos. Exporte as evidências antes de remover esse volume.

## Primeiro exercício

1. Crie S01, perfil A, com roteiro fixo.
2. Execute e examine `tool.executed` e `evaluator.verdict`.
3. Confira o acesso ao ticket de outro cliente no estado final.
4. Baixe as evidências do episódio.
5. Repita S01 no perfil B e compare a negativa do servidor.
6. Execute o controle benigno em ambos os perfis.
7. Registre sua explicação e cite os artefatos usados.

O arquivo `state-after.json` registra efeitos do alvo. `utility-proof.json` avalia a tarefa legítima de cada cenário.

Um roteiro conhece o caso antes da execução. Ele valida mecanismos e infraestrutura; conclusões sobre descoberta autônoma exigem outro desenho experimental.

## Executar sem Docker

```bash
rbf serve
```

O comando informa o caminho do arquivo `control-token`. Leia esse arquivo localmente para entrar no painel.

Os cenários usam o FieldDesk local. S12 e a bancada de ferramentas precisam dos alvos Docker.

Para executar um episódio pelo terminal:

```bash
rbf demo --scenario S11 --profile A
rbf demo --scenario S11 --profile B
rbf doctor
```

## Escolher o modo

| Modo | Comportamento |
| --- | --- |
| `manual` | A pessoa propõe hipóteses e conduz ações no escopo do episódio. |
| `scripted` | Um roteiro fixo executa o caso conhecido. |

O Codex local pode apoiar a investigação e a interpretação das evidências. Os antigos chats próprios e a proxy foram retirados; sua documentação histórica não descreve o fluxo atual.

## Intervenção humana

Crie S04 no perfil D com revisão humana. Execute até surgir uma operação pendente.

Examine ação, parâmetros e identificação criptográfica. Registre sua justificativa ao aprovar ou negar; depois execute outro passo.

A aprovação cobre um episódio, escopo, operação e versão do estado. Mudanças nesses elementos exigem outra decisão.

O consumo da decisão precede o envio da operação. Uma falha entre essas etapas exige reconciliação; a aplicação interrompe a tentativa.

O alvo de reembolso também exige sua própria aprovação vinculada. Ele consome essa aprovação na mesma transação que registra o reembolso.

Uma aprovação humana permite tentar a operação. Os controles do alvo continuam aplicáveis.

## Ferramentas disponíveis

Selecione S11 ou S12 e abra a bancada. Os perfis aceitam nomes fixos; cada comando aponta para recursos sintéticos do contêiner.

| Perfil | Exercício |
| --- | --- |
| `nmap_local` | Identificar o serviço da porta 8080 do próprio contêiner. |
| `sqlmap_fixture` | Verificar a consulta sintética vulnerável do contêiner. |
| `http_headers` | Inspecionar a resposta HTTP local. |
| `filesystem` | Examinar a pasta de marcadores do alvo. |
| `system` | Observar informações do sistema descartável. |
| `crypto` | Conferir a versão do OpenSSL. |
| `python` | Calcular uma impressão criptográfica de dados sintéticos. |
| `network` | Inspecionar interfaces do próprio contêiner. |
| `metasploit_version` | Informar indisponibilidade na imagem padrão. |

A bancada conserva saída, erros e código de retorno. A prova do S12 usa um marcador separado, criado apenas no alvo vulnerável.

Os resultados da bancada descrevem o serviço do contêiner. Uma conclusão sobre outro alvo exige evidência desse alvo.

O [inventário de referência](../research/pentagi-tool-inventory.json) mantém as famílias do PentAGI. A imagem padrão instala um conjunto menor, descrito acima.

## Evidências e reinício

O pacote contém manifesto, escopo, estados, eventos, hipóteses, fronteira pendente e resultado. Revisões e avaliações registradas também acompanham o episódio.

```bash
rbf verify artifacts/private/runs/IDENTIFICADOR
```

O verificador confere contratos, arquivos, sequência, vínculos e impressões criptográficas. Uma cadeia válida detecta alterações acidentais; um administrador do disco pode reescrever toda a cadeia.

Use assinatura externa ou armazenamento imutável quando precisar de auditoria com esse nível de confiança.

Após reiniciar, episódios concluídos permitem consulta e exportação. Tentativas abertas ficam interrompidas; suas credenciais perdem validade.

Uma coleta incompleta exige reconciliação. O aplicativo preserva os arquivos e rejeita a exportação validada quando o manifesto falha.

## Campanhas e aprendizado

O painel executa campanhas pareadas com cenários, perfis e controles benignos. A interface de programação de aplicações (API) permite escolher repetições e orçamento.

O resumo separa episódios válidos, desconhecidos, efeitos adversariais e tarefas benignas. Os dados individuais permitem calcular resultados por configuração.

Encerre o episódio antes de avaliar aprendizado. Cite evidências, explique o mecanismo, registre ajuda recebida e descreva lacunas.

O relatório de aprendizado reúne resultado, intervenções e avaliações do operador. Uma revisão externa exige identificar e registrar outra pessoa responsável.

## Testes da aplicação

```bash
pytest -q
docker build -f docker/worker.Dockerfile -t red-blue-field-worker:0.4.0 .
RBF_TEST_DOCKER=1 pytest -q tests/test_docker.py
pip install -e '.[browser]'
python -m playwright install chromium
RBF_TEST_BROWSER=1 pytest -q tests/test_browser.py
```

Os testes Docker criam rede interna e contêineres próprios. Ao terminar, removem somente esses recursos.

Em redes com autoridade certificadora própria, configure o certificado no ambiente de construção. Os Dockerfiles aceitam o segredo BuildKit `system_ca`.
