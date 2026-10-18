# Validação da revisão 0.2

Data: 18/10/2026. Escopo: pesquisa, planejamento e contratos propostos; não validação de sistemas executáveis.

- Oito schemas conferidos como JSON Schema Draft 2020-12, incluindo referências entre manifesto/episódio e contexto do estudo.
- Dezoito cenários validados; IDs únicos e referências resolvem para 32 fontes públicas. PentAGI e Cloudflare têm revisões de código registradas no índice.
- Seis eventos ilustrativos, um episódio não executado, escopo e manifesto validados. Estado, contexto, spans, referências, cadeia de hashes e checksums conferidos.
- Treze variantes inválidas rejeitadas: sucesso, validade ou drift em exemplo ilustrativo; exemplo promovido a model run; perfil D sem revisor; modelo sem configuração; sucesso sem prova; cloud ativo sem revisão de política; achado confirmado sem prova runtime; pendência com severidade ou sem condição decisiva; cobertura completa com unidade pendente; ambiente desconhecido.
- Entradas sintéticas de validação exercitaram os três estados de achados e cobertura completa/incompleta. Permanecem fora do corpus publicado e não são resultados de auditoria ou pentest.
- Links relativos, sete seções do formato to-spec, dependências sem ciclos e correspondência entre mirrors e corpos publicados conferidos.
- Busca por referências privadas específicas do contexto e padrões comuns de credenciais sem ocorrências nos padrões analisados. Isso não substitui a revisão de futuros exports.
- Dezesseis issues relidas no GitHub: títulos, corpos e estados conferidos. Nove atualizadas e sete criadas; pesquisa inicial encerrada, quinze issues abertas. A entrega inicial permanece vinculada ao snapshot 0.1.

A checagem de contratos usou Python, `jsonschema` e `referencing`, com resolução local dos schemas. Verifica estrutura e consistência documental; os exemplos continuam `illustrative`/`not_executed` e sem métricas.

Nenhuma ferramenta de pentest, plataforma PentAGI, skill de auditoria, aplicação ou agente foi executado. Não houve provisionamento cloud. Isolamento, autorização, validade operacional do escopo, autenticidade da coleta, independência efetiva do verificador, contenção e recuperação precisam de testes na implementação. Os schemas não comprovam a verdade de um achado nem a existência da evidência referenciada.
