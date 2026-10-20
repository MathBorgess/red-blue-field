# Validação da revisão 0.3

Data: 20/10/2026. Escopo: documentos, contratos, exemplos e backlog. Execução de agentes e servidores permanece pendente.

## Contratos e exemplos

- Nove schemas conferidos como `JSON Schema Draft 2020-12`.
- Dezoito cenários validados e referências resolvidas para 36 fontes públicas.
- Nove famílias de ferramentas extraídas do prompt PentAGI fixado por commit.
- Inventário permanece documentado, com disponibilidade instalada pendente de teste.
- Seis eventos, um episódio e uma hipótese ilustrativa validados.
- Escopo, contexto, artefatos e cadeia de hashes conferidos.
- Vinte combinações inválidas rejeitadas, incluindo sete casos do novo contrato de hipótese.
- Links locais, seções da to-spec e correspondência da spec com a issue principal conferidos.
- Busca por padrões de credenciais e referências privadas específicas sem ocorrências nos padrões analisados.

Os contratos anteriores permanecem em 0.2. O novo contrato de hipótese usa 0.3; seus estados ilustrativos preservam ausência de execução.

Os casos sintéticos de validação ficam fora do dataset publicado. Eles verificam formato e consistência, sem representar experimentos de segurança.

## Linear e documentação

- Projeto dedicado no time Mathai, com 18 tarefas e uma tarefa principal.
- Títulos, descrições completas, estados e vínculos de parentesco conferidos por leitura de retorno.
- Dezoito conjuntos de dependências conferidos, com grafo sem ciclos.
- Todas as tarefas em Backlog; execução e avaliação permanecem futuras.
- Textos novos e documentos alterados passaram no linter de linguagem simples, com perfil português e glossário do projeto.

O [recibo do Linear](../planning/linear-backlog.json) registra identificadores e a data de verificação. As descrições mantêm critérios de aprendizado e evidência.

O Linear normaliza a marcação de links. A comparação de conteúdo preservou o texto e normalizou apenas os delimitadores dos endereços.

## Limites da checagem

A validação usou Python, `jsonschema`, `referencing` e o linter da easy-to-read. A implementação futura deverá testar busca, integração e autorização efetivas.

Isolamento, execução das ferramentas, conexão dos servidores, contenção e supervisão humana aguardam provas práticas. Os schemas verificam estrutura; a verdade de um achado exige evidência.

O [modelo final](final-learning-report-template.md) conserva notas e parecer pendentes. O marco de domínio depende da avaliação humana definida no plano.
