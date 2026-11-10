# S02 with a separate real target

The operator and the target are separate roles. The operator helps the researcher formulate a hypothesis and inspect evidence. The target tries to complete a legitimate task using the configured model and a closed set of synthetic tools. The FieldDesk controller authorizes operations and applies their effects.

Existing manual/scripted episodes continue to use the deterministic fixture by default. Selecting an external target does not silently fall back to that fixture if the model is unavailable.

## Deployment and credentials

The controller enables the real S02 driver explicitly with `RBF_ENABLE_REAL_TARGET=1`. Its persistent pilot ledger is identified by `RBF_REAL_TARGET_PILOT_ID=s02-pilot`. Disabling the driver does not delete or reset that ledger.

The model worker runs separately from the controller. It needs a dedicated OpenAI API key and a **target** token for one episode. The operator bridge uses a **red** token for that episode. The researcher retains the controller credential. Never put any of these values in a prompt, URL, tracked config or screenshot.

The example architecture uses an HTTPS origin behind Cloudflare Access. Both clients use the researcher's authorized Access session and retain the separate FieldDesk role token. Expired Access credentials require human sign-in. No Service Auth or Bypass policy is needed. The controller does not require outgoing access to the model provider or a public listener on the worker machine.

Files containing role tokens must be private regular files with mode `0600`. They contain the opaque token only. The API key belongs in the worker's private environment or an ignored env file, never in the controller VM or operator MCP arguments.

Processes running as the same OS user are not isolated from each other's files by `0600`. The operator is a trusted, supervised researcher. The target model receives only synthetic input and structured tools; it has no host shell or filesystem tool.

## Bounded pilot

The initial rate card uses `gpt-5.4-mini-2026-03-17`: USD 0.75 per million input tokens and USD 4.50 per million output tokens, checked on 2026-11-10. Account access and current tariffs must be checked before live execution. [Model documentation](https://developers.openai.com/api/docs/models/gpt-5.4-mini).

The pilot has a persistent USD 1.00 ceiling, at most four episodes, USD 0.20 and four model requests per episode, and twenty requests in total including technical checks. Each request allows at most 12,000 input tokens and 2,000 output tokens. Under these base prices and bounds, twenty requests total at most USD 0.36 in estimated token cost. This is a calculation, not a billing receipt.

Before submitting a model request, the worker counts its complete input and obtains a central reservation. Requests cannot reuse that submission authorization. Unknown charges retain their reservation and block further pilot work. No automatic retry follows a timeout or uncertain provider result. A restart must not reset the budget. Provider account limits are an additional control, not the sole per-experiment budget.

## Researcher workflow

1. Prepare the legitimate task, hypothesis and falsification criterion before creating the episode.
2. In the UI, select **S02**, **Manual** and **Agente real · API externa**. Set the absolute episode deadline; creation itself does not submit a model request.
3. Configure the episode's operator and target tokens using the controller-only credential operation. Keep those files out of captured screens and version control.
4. First validate MCP discovery and scope reading without requesting a model or applying a mutation.
5. Start with the benign task. The researcher authorizes one model request from the UI. The worker processes the approved job, then returns its public response or proposed function and usage.
6. Inspect the proposed function, arguments, operation identity and current state. **Tentar função proposta** attempts it through the backend authorization policy; it does not grant new business permission.
7. Correlate the tool decision and effect, then authorize a continuation only if needed. No inference runs while the researcher inspects the evidence.
8. Stop or finish the episode, record the interpretation and assistance received, then export the evidence.

Only after validating the benign path should the researcher propose an adversarial variant. Keep the same model, prompt, tool catalog and input when comparing backend controls. A known deterministic fixture recipe is not autonomous discovery or a measurement of a real model.

## Clients

Install the project in a Python 3.12 environment. These commands are examples: replace the endpoint, episode ID and private file paths with the approved local configuration. They do not provision credentials.

```sh
rbf-mcp-remote --endpoint https://lab.example.test --run-id EPISODE_ID \
  --role red --role-token-file /private/fielddesk/red-token
```

The bridge speaks MCP over stdio. It forwards to the remote FieldDesk; the legacy `rbf-mcp-red` executable creates a different local Lab and is not a replacement for this bridge.

```sh
rbf-target-worker --endpoint https://lab.example.test --run-id EPISODE_ID \
  --role-token-file /private/fielddesk/target-token --env-file .env.local --once
```

The default worker handles one approved job. It neither approves its own next request nor applies tool effects. Do not run it against an unreviewed endpoint or share the controller token with it.

Example Codex registration, initially disabled and containing no credential values:

```toml
[mcp_servers.fielddesk_s02]
command = "rbf-mcp-remote"
args = ["--endpoint", "https://lab.example.test", "--run-id", "EPISODE_ID", "--role", "red", "--role-token-file", "/private/fielddesk/red-token"]
enabled = false
enabled_tools = ["red.get_scope", "red.get_run", "red.get_evidence", "red.propose_hypothesis", "red.test_agent", "red.stop_run"]
default_tools_approval_mode = "prompt"
```

Confirm the configuration against the installed client's supported schema before enabling it. Tool discovery in a protocol test does not itself establish that a Desktop session loaded the integration. [Official MCP configuration](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).

## Evidence and interruption

Record episode/job IDs, frozen configuration, request/response IDs, reported usage, estimated cost, tool proposal, policy decision and effect separately. Do not persist private reasoning or opaque continuation items in public traces or exports. The model API uses `store=false`; this is not a claim of zero provider retention.

Stopping invalidates further target operations. Results arriving after the stop cannot apply an effect. A cancelled local request may already have been processed or charged by the provider, so preserve its reservation and reconcile it before trying again. Restoring fixture data does not reset the episode clock, hypotheses or spend ledger.

For content capture, show the hypothesis before execution, one public proposal, its policy decision, the correlated effect and the researcher's explanation. Keep credentials and identity/account screens out of the recording. Label mocked transport tests and deployment checks as such; they are not real-model security results.
