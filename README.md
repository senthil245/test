# agent-maint

A maintenance toolkit for a fleet of LLM agents. Each agent is declared as code (a TOML manifest plus a prompt file), and `agent-maint check` runs these checks on every PR and weekly in CI:

| Check | Catches | Severity |
|---|---|---|
| `model_lifecycle` | Agents pinned to deprecated, soon-retiring, retired or unregistered models | warn → error on retirement date |
| `prompt_drift` | Prompt edits that skipped review/evals (manifest hash ≠ file) | error |
| `config_lint` | Missing `max_tokens`, out-of-range temperature, unroutable owner, no evals | warn / error |
| `tool_schema` | Invalid or duplicate tool names, thin descriptions, broken JSON Schema | warn / error |
| `eval_regression` | Metrics worse than the committed baseline beyond each metric's tolerance | error |

The scheduled run matters: a model retirement date can arrive without anyone touching the code.

## Layout

```
agents/<name>/agent.toml    # manifest: model, owner, params, tools, eval tolerances
agents/<name>/prompt.md     # system prompt (hash-pinned in the manifest)
config/model_lifecycle.toml # model status / retirement dates / replacements
evals/baselines/<name>.json # accepted metrics
evals/results/<name>.json   # latest run (written by CI / your eval harness)
src/agent_maint/            # library + CLI
docs/RUNBOOK.md             # how to respond to each finding
.github/workflows/agent-maintenance.yml
```

## Quick start

```bash
pip install -e ".[dev]"
```

```bash
agent-maint list
```

```bash
agent-maint check                                  # text report, exits 1 on any error
```

```bash
agent-maint check --format markdown --output reports/maintenance-report.md
```

```bash
agent-maint lock                                   # re-pin prompt hashes after an approved prompt change
```

Options for `check`: `--only <check>` (repeatable), `--format text|markdown|json`, `--fail-on error|warn|never`, `--today YYYY-MM-DD` (to simulate future retirement dates).

Exit codes: `0` ok, `1` findings at or above `--fail-on`, `2` invalid manifest.

## Adding an agent

1. Copy `agents/support-triage/` to `agents/<new-name>/` and edit `agent.toml` and `prompt.md`.
2. Make sure the model is listed in `config/model_lifecycle.toml`.
3. Run your eval suite and commit `evals/baselines/<new-name>.json`.
4. Run `agent-maint lock`, then `agent-maint check`, then open a PR.

## Adding a check

Write a function `(agent: AgentSpec, ctx: RunContext) -> list[Finding]` in `src/agent_maint/checks/`, register it in `checks/__init__.py:ALL_CHECKS`, and add tests in `tests/test_checks.py`.

## Not yet included

- **Eval harness**: the workflow has a placeholder step. Point it at your harness so it writes `evals/results/`.
- **Lifecycle data**: `config/model_lifecycle.toml` is a starting point. Keep it in sync with your providers' deprecation notices.
