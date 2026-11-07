"""Run checks across the fleet."""

from __future__ import annotations

from collections.abc import Iterable

from .checks import ALL_CHECKS
from .context import RunContext
from .models import AgentSpec, Finding, Severity


def run(agents: Iterable[AgentSpec], ctx: RunContext, only: Iterable[str] | None = None) -> list[Finding]:
    selected = list(only) if only else list(ALL_CHECKS)
    unknown = set(selected) - set(ALL_CHECKS)
    if unknown:
        raise ValueError(f"unknown checks: {', '.join(sorted(unknown))}")
    findings: list[Finding] = []
    for agent in agents:
        for name in selected:
            try:
                findings.extend(ALL_CHECKS[name](agent, ctx))
            except Exception as exc:  # a broken check must not hide the others
                findings.append(Finding(name, agent.name, Severity.ERROR, f"check crashed: {exc!r}"))
    findings.sort(key=lambda f: (-f.severity, f.agent, f.check))
    return findings


def worst(findings: list[Finding]) -> Severity:
    return max((f.severity for f in findings), default=Severity.OK)
