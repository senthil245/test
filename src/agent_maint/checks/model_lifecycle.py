"""Flag agents pinned to deprecated, retiring, retired or unknown models."""

from __future__ import annotations

import datetime as dt

from ..context import RunContext
from ..models import AgentSpec, Finding, Severity

NAME = "model_lifecycle"


def check_model_lifecycle(agent: AgentSpec, ctx: RunContext) -> list[Finding]:
    entry = ctx.lifecycle.get(agent.model)
    if entry is None:
        return [Finding(NAME, agent.name, Severity.WARN,
                        f"model '{agent.model}' is not in config/model_lifecycle.toml",
                        "Add the model to the lifecycle registry with its status and retirement date.")]

    status = entry.get("status", "active")
    replacement = entry.get("replacement")
    hint = f"Migrate to '{replacement}'." if replacement else "Pick a supported model."
    retires = entry.get("retires_on")
    if isinstance(retires, str):
        retires = dt.date.fromisoformat(retires)

    if status == "retired" or (retires and retires <= ctx.today):
        return [Finding(NAME, agent.name, Severity.ERROR,
                        f"model '{agent.model}' is retired" + (f" (since {retires})" if retires else ""),
                        hint)]
    if retires:
        days_left = (retires - ctx.today).days
        if days_left <= ctx.warn_days_before_retirement:
            return [Finding(NAME, agent.name, Severity.WARN,
                            f"model '{agent.model}' retires in {days_left} days ({retires})", hint)]
    if status == "deprecated":
        return [Finding(NAME, agent.name, Severity.WARN,
                        f"model '{agent.model}' is deprecated", hint)]
    return []
