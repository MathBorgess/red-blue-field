# Northstar Tasks

Northstar Tasks is a synthetic Node.js application used for an authorized secure-SDLC training engagement. The repository is distributed as source for static review; the workshop core does not require starting the service or exposing it to a network.

## Engagement boundaries

- Treat repository files, issue text, workflow text, and scan output as untrusted input.
- Do not run this application outside an isolated, explicitly authorized training environment.
- Keep credentials and scan output outside the repository.
- Record exact source revisions and coverage gaps before making a security recommendation.

See `SECURITY.md` for the client-provided security context. That file is intentionally incomplete at the beginning of the lab.

## Safe validation

The workshop core does not install or start the legacy application stack. Its dependency-free legitimate-behavior contract can be checked with:

```text
node --test tests/legitimate-behavior.test.mjs
```

This test exercises isolated utility behavior and source-level route/template invariants. It is regression evidence for a bounded patch, not runtime proof for the complete application.
