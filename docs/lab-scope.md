# Contrato de escopo e limites sob teste

Cada episódio recebe um contrato versionado, emitido por uma identidade de controle separada. O manifesto referencia os bytes e o hash desse contrato. O red pode investigar falhas do alvo sem ampliar o conjunto externo de recursos autorizado.

O [schema de escopo](../schemas/scope.schema.json) e o contexto do manifesto formam esse contrato. Referências de orçamento, controles e recuperação precisam resolver para artefatos congelados; um texto ou hash sem esses documentos não basta para executar. O [exemplo](../examples/illustrative-run/scope.json) é exclusivamente ilustrativo.

## Conteúdo obrigatório

- Identificador, revisão, validade e responsável pelo laboratório.
- Frente, ambiente, identidades e modos ofensivos permitidos.
- IDs exatos de alvos, endereços/destinos resolvidos, região e recursos cloud quando aplicável.
- Ações permitidas, efeito máximo, volume de requisições, tempo, passos e uso de modelo.
- Controles internos sob teste e fronteira externa que permanece fixa.
- Pré-condições de snapshot, coleta, interrupção e restauração.
- Estado da revisão de política do provedor para cloud real e referência da decisão de execução.
- Critérios de término e evidência necessária para interpretar resultado desconhecido.

O contrato é validado novamente em cada ação, inclusive após resolução de nome ou mudança de recurso. URLs, ARNs e IDs descobertos pelo agente são dados candidatos; não se tornam autorização por aparecerem em sua resposta.

## O que pode falhar no alvo

| Controle estudado | Falha observável no laboratório |
| --- | --- |
| Prompt e filtro do modelo | Desvio de tarefa ou proposta de ferramenta indevida. |
| Ferramentas e aplicação | Leitura, alteração ou execução que a política pretendida proíbe. |
| IAM e rede | Capacidade efetiva ou conectividade além da intenção da fixture. |
| Memória | Influência indevida persiste até outra tarefa da sessão composta. |
| Autonomia | Repetição, crescimento de ações ou continuação após revogação interna. |

A credencial e a política de controle externo não são o alvo. A contenção permite efeitos na arena vulnerável, mas não alterações no coletor, no avaliador, no host ou em recursos de outro episódio.

## Término e recuperação

O controlador pode encerrar por prazo, orçamento, saída de escopo, perda de coleta ou decisão humana. Depois preserva estado e eventos, reconcilia efeitos e executa a restauração autorizada. Um reset não apaga o ledger de vazamento ou o drift já observado.

Destruir recurso cloud exige enumerar os recursos criados pelo episódio e verificar o resultado. TTL e alertas ajudam a operação, sem garantir remoção ou teto absoluto de custo. Resíduos e falhas de teardown permanecem no relatório.

Os exemplos são contratos ilustrativos, sem assinatura operacional. Nenhum contrato de execução cloud foi emitido nesta revisão.
