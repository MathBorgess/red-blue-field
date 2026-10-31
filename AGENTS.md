# red-blue-field — guia para agentes

Este repositório é um laboratório de segurança conduzido pelo Codex Desktop. Comece pelo [README](README.md) e pelo [vocabulário](GLOSSARY.md).

- Consulte [SPEC.md](SPEC.md) e [o estado da implementação](docs/implementation-status.md) antes de alterar o comportamento do laboratório.
- RED reúne ferramentas de investigação; BLUE reúne defesa, resposta e verificação de achados; FIELD reúne alvos e cenários. Defina alvo, ações e limites de cada atividade autorizada.
- Os recursos e alvos de cada episódio permanecem limitados pelo controlador. Respeite as regras específicas de cada alvo e os limites do provedor.
- Preserve a distinção entre execução manual, roteiro fixo, emulação cloud e registros históricos de modelos. Não atribua observações de simulação a um modelo real.
- Registre hipóteses, critérios de refutação, observações e efeitos. Não registre raciocínio privado do modelo, credenciais ou traces brutos no repositório público.
- Preserve arquivos e assinaturas de evidências existentes; alterações em como são lidos ou gravados exigem validação de compatibilidade.
- O Northstar em `FIELD/codex-security-client-app/` é um alvo separado do FieldDesk. Leia seu README e SECURITY.md antes de trabalhar nele.
- Consulte [execução do laboratório](docs/running-the-lab.md) e [MCP](docs/mcp-red-blue.md) para os comandos e limites atuais. Testes internos não comprovam compatibilidade com o Codex Desktop.

Para validar alterações, execute os testes relevantes e `.venv/bin/python -m pytest -q` quando o ambiente estiver disponível. Ao mudar comandos ou configuração, atualize o README e `.env.example`.
