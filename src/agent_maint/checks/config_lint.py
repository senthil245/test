"""Sanity-check generation parameters and ownership metadata."""

from __future__ import annotations

from ..context import RunContext
from ..models import AgentSpec, Finding, Severity

NAME = "config_lint"


def check_config(agent: AgentSpec, ctx: RunContext) -> list[Finding]:
    out: list[Finding] = []
    if "@" not in agent.owner and not agent.owner.startswith("team:"):
        out.append(Finding(NAME, agent.name, Severity.WARN,
                           f"owner '{agent.owner}' is not an email or team:<name> handle",
                           "Use a routable owner so alerts reach someone."))
    if agent.max_tokens is None:
        out.append(Finding(NAME, agent.name, Severity.WARN, "params.max_tokens is not set",
                           "Set an explicit max_tokens to bound cost and latency."))
    elif agent.max_tokens <= 0:
        out.append(Finding(NAME, agent.name, Severity.ERROR, f"params.max_tokens must be > 0 (got {agent.max_tokens})"))
    if agent.temperature is not None and not 0.0 <= agent.temperature <= 1.0:
        out.append(Finding(NAME, agent.name, Severity.ERROR,
                           f"params.temperature {agent.temperature} is outside [0, 1]"))
    if not agent.evals:
        out.append(Finding(NAME, agent.name, Severity.WARN, "no [evals] section; regressions cannot be detected",
                           "Add an eval suite and baseline."))
    return out
