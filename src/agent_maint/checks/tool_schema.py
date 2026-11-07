"""Validate tool definitions: names, descriptions and JSON-Schema shape."""

from __future__ import annotations

import re

from ..context import RunContext
from ..models import AgentSpec, Finding, Severity

NAME = "tool_schema"
TOOL_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
MIN_DESCRIPTION = 20


def check_tool_schemas(agent: AgentSpec, ctx: RunContext) -> list[Finding]:
    out: list[Finding] = []
    seen: set[str] = set()
    for tool in agent.tools:
        label = tool.name or "<unnamed>"
        if not TOOL_NAME_RE.match(tool.name):
            out.append(Finding(NAME, agent.name, Severity.ERROR,
                               f"tool '{label}' has an invalid name (must match {TOOL_NAME_RE.pattern})"))
        if tool.name in seen:
            out.append(Finding(NAME, agent.name, Severity.ERROR, f"duplicate tool name '{label}'"))
        seen.add(tool.name)

        if len(tool.description.strip()) < MIN_DESCRIPTION:
            out.append(Finding(NAME, agent.name, Severity.WARN,
                               f"tool '{label}' description is too short to guide the model",
                               "Describe what the tool does, when to use it, and what it returns."))

        schema = tool.input_schema
        if schema.get("type") != "object":
            out.append(Finding(NAME, agent.name, Severity.ERROR,
                               f"tool '{label}' input_schema.type must be 'object'"))
            continue
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in props:
                out.append(Finding(NAME, agent.name, Severity.ERROR,
                                   f"tool '{label}' requires '{req}' but it is not in properties"))
        for pname, pdef in props.items():
            if not isinstance(pdef, dict) or "type" not in pdef:
                out.append(Finding(NAME, agent.name, Severity.WARN,
                                   f"tool '{label}' property '{pname}' has no type"))
            elif not pdef.get("description"):
                out.append(Finding(NAME, agent.name, Severity.INFO,
                                   f"tool '{label}' property '{pname}' has no description"))
    return out
