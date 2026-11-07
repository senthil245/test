"""Render findings as text, Markdown or JSON."""

from __future__ import annotations

import json
from collections import Counter

from .models import AgentSpec, Finding, Severity

ICON = {Severity.ERROR: "❌", Severity.WARN: "⚠️", Severity.INFO: "ℹ️", Severity.OK: "✅"}


def _summary(findings: list[Finding]) -> Counter:
    return Counter(f.severity.label for f in findings)


def render_text(agents: list[AgentSpec], findings: list[Finding]) -> str:
    c = _summary(findings)
    lines = [f"agent-maint: {len(agents)} agents, "
             f"{c['error']} errors, {c['warn']} warnings, {c['info']} info"]
    for f in findings:
        lines.append(f"  [{f.severity.label.upper():5}] {f.agent:<20} {f.check:<16} {f.message}")
        if f.remediation:
            lines.append(f"  {'':7} {'':<20} {'':<16} -> {f.remediation}")
    return "\n".join(lines)


def render_markdown(agents: list[AgentSpec], findings: list[Finding]) -> str:
    c = _summary(findings)
    out = ["# Agent maintenance report", "",
           f"**{len(agents)} agents** · {c['error']} errors · {c['warn']} warnings · {c['info']} info", "",
           "## Fleet", "", "| Agent | Owner | Model | Status |", "|---|---|---|---|"]
    by_agent: dict[str, Severity] = {}
    for f in findings:
        by_agent[f.agent] = max(by_agent.get(f.agent, Severity.OK), f.severity)
    for a in agents:
        sev = by_agent.get(a.name, Severity.OK)
        out.append(f"| {a.name} | {a.owner} | `{a.model}` | {ICON[sev]} {sev.label} |")
    out += ["", "## Findings", ""]
    if not findings:
        out.append("No findings. 🎉")
    else:
        out += ["| Severity | Agent | Check | Finding | Remediation |", "|---|---|---|---|---|"]
        for f in findings:
            msg = f.message.replace("|", "\\|")
            fix = (f.remediation or "").replace("|", "\\|")
            out.append(f"| {ICON[f.severity]} {f.severity.label} | {f.agent} | {f.check} | {msg} | {fix} |")
    return "\n".join(out) + "\n"


def render_json(agents: list[AgentSpec], findings: list[Finding]) -> str:
    return json.dumps({
        "agents": [{"name": a.name, "owner": a.owner, "model": a.model} for a in agents],
        "summary": dict(_summary(findings)),
        "findings": [f.to_dict() for f in findings],
    }, indent=2)


RENDERERS = {"text": render_text, "markdown": render_markdown, "json": render_json}
