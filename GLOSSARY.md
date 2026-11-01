# Vocabulário

**Field**:
Conjunto de alvos e cenários para investigação e exercícios autorizados.

| Termo | Significado no laboratório |
| --- | --- |
| Aplicação alvo | Aplicação incluída no escopo de uma investigação ou exercício. |
| FieldDesk | Serviço fictício e seu assistente de produto. |
| Red team | Papel que investiga e testa hipóteses adversariais dentro do escopo autorizado. |
| Blue team | Papel que verifica achados, investiga sinais e atua na defesa e na resposta com permissões explícitas. |
| Controlador | Software externo aos agentes que impõe escopo, orçamento, sequência e interrupção. |
| Avaliador / oráculo | Verificador que usa efeitos e estado da aplicação para classificar resultados. |
| Cenário | Contrato versionado de tarefa legítima, objetivo adversarial, capacidade permitida e evidência necessária. |
| Episódio | Uma tentativa limitada de um cenário, com estado inicial isolado e um resultado terminal. |
| Campanha | Conjunto de episódios agrupados por configuração experimental. |
| Perfil de defesa | Conjunto congelado de políticas, ferramentas e permissões usado em um grupo experimental. |
| Trace | Grafo de spans e eventos que permite acompanhar a execução entre componentes. |
| Proveniência | Origem e transformações de uma entrada, evento ou artefato. |
| Canary | Marcador sintético exclusivo que ajuda a verificar acesso ou saída indevidos. |
| Sink | Destino local que registra uma saída simulada; não envia dados para terceiros. |
| HITL | Human in the loop: decisão de uma pessoa antes de uma ação específica. |
| Aprovação vinculada | Decisão ligada a identidade, ação, parâmetros, versão do recurso, prazo e uso único. |
| Replay | Reprodução de entradas e chamadas registradas. Não implica que uma nova chamada ao LLM terá o mesmo resultado. |
| Prompt injection | Conteúdo que tenta transformar dados não confiáveis em instruções para um modelo. |
| Tool poisoning | Instruções adversariais em metadados ou descrições de ferramentas. |
| BOLA / IDOR | Acesso a um objeto sem a autorização exigida, frequentemente por alteração de seu identificador. |
| Identidade de workload | Identidade criptográfica de um serviço ou processo em execução, distinta da identidade da pessoa em nome de quem ele age. |
| Atestação de workload | Verificação de atributos observados de um processo antes de lhe atribuir uma identidade de workload. |
| SPIFFE ID | Identificador de um workload em um domínio de confiança; sua posse não concede acesso a todo dado ou ação. |
| JWT-SVID | Credencial JWT assinada que representa um SPIFFE ID para uma audiência e um prazo definidos. |
| Federação de identidade de workload (WIF) | Uso de uma identidade de workload verificada para obter ou exercer uma credencial em outro serviço ou domínio de confiança. |
| Concessão de tarefa | Autorização limitada que vincula pessoa, workload, ação, recurso e prazo a uma tarefa específica. |
| Estado da evidência | Observado, demonstrado, relatado por fornecedor, hipotético ou não executado. |
| Pentest com agentes | Uso de agente para investigar e confirmar falhas em serviços; o alvo pode funcionar sem IA. |
| Agentic red teaming | Avaliação adversarial de objetivos, decisões, ferramentas, memória e autonomia de um agente. |
| Cadeia híbrida | Falha de serviço e influência sobre agente compõem um caminho com cada transição comprovada. |
| Agência / autonomia | Capacidades de agir concedidas / independência para decidir como e quando agir. |
| Black / gray / white box | Acesso externo / informação parcial / código e arquitetura autorizados; condições de estudo diferentes. |
| Desvio / comprometimento / drift | Comportamento fora da tarefa / efeito indevido confirmado no serviço / mudança de configuração observada. |
| Verificador de achados | Papel que reconstrói uma alegação e confere suas evidências; pode ser exercido pelo Blue team. |
| Ledger de cobertura | Registro de unidades e verificações por revisão; ausência de achados não comprova cobertura total. |
