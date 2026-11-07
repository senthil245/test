# Agent maintenance runbook

## Cadence

| When | What | Who |
|---|---|---|
| Every PR touching agents/config/evals | `agent-maint check` gates the merge | PR author |
| Weekly (Mon, scheduled CI) | Full check and report in the job summary | Rotating agent-ops owner |
| Monthly | Review `config/model_lifecycle.toml` against provider deprecation notices; refresh baselines if traffic has shifted | Agent platform team |
| Quarterly | Prune unused agents/tools; review owners; check cost per agent | Agent platform team + owners |

## Responding to findings

### `model_lifecycle`
- **Unregistered model (warn):** add it to `config/model_lifecycle.toml` with its status.
- **Deprecated / retiring soon (warn):** open a migration ticket for the agent owner. Run evals on the replacement model, compare against the baseline, then update `model` in the manifest along with the new baseline.
- **Retired (error):** the agent is failing or about to fail in production. Treat it as an incident: migrate now and backfill evals afterwards.

### `prompt_drift`
- **Hash mismatch (error):** someone changed the prompt without re-locking. Run evals on the new prompt. If they pass, run `agent-maint lock` and commit the new hash in the same PR. If they don't, revert the prompt.
- **No hash pinned (warn):** run `agent-maint lock`.

### `config_lint`
- Fix the parameter in `agent.toml`. An unroutable owner means alerts go nowhere, so use an email or `team:<name>`.

### `tool_schema`
- Errors break tool calls at runtime, so fix them before merging.
- Short or missing descriptions lower tool-selection accuracy. Say what the tool does, when to call it, and what it returns.

### `eval_regression`
1. Confirm the regression is real: re-run the suite and check for flaky cases.
2. Bisect across the prompt, model and tool changes in the PR.
3. If the change is intended (for example, a deliberate latency-for-accuracy trade), update `evals/baselines/<agent>.json` in a separate commit and explain why in the PR.

## Escalation
- An error finding on `main` from the scheduled run: page the agent owner listed in the manifest.
- A retired model in production: escalate to the agent platform on-call.
