"""Discover and parse agent manifests."""

from __future__ import annotations

import tomllib
from pathlib import Path

from .models import AgentSpec, ToolSpec


class ManifestError(ValueError):
    pass


REQUIRED_KEYS = ("name", "owner", "model")


def load_agent(manifest: Path) -> AgentSpec:
    try:
        data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ManifestError(f"{manifest}: invalid TOML: {exc}") from exc

    agent = data.get("agent", {})
    missing = [k for k in REQUIRED_KEYS if not agent.get(k)]
    if missing:
        raise ManifestError(f"{manifest}: missing required [agent] keys: {', '.join(missing)}")

    tools = [
        ToolSpec(
            name=t.get("name", ""),
            description=t.get("description", ""),
            input_schema=t.get("input_schema", {}),
        )
        for t in data.get("tools", [])
    ]
    params = data.get("params", {})
    return AgentSpec(
        name=agent["name"],
        owner=agent["owner"],
        model=agent["model"],
        root=manifest.parent,
        prompt_file=agent.get("prompt_file", "prompt.md"),
        prompt_sha256=agent.get("prompt_sha256"),
        max_tokens=params.get("max_tokens"),
        temperature=params.get("temperature"),
        tools=tools,
        evals=data.get("evals", {}),
        raw=data,
    )


def discover(agents_dir: Path) -> list[AgentSpec]:
    """Load every agents/*/agent.toml, sorted by name."""
    if not agents_dir.is_dir():
        raise ManifestError(f"agents directory not found: {agents_dir}")
    specs = [load_agent(p) for p in sorted(agents_dir.glob("*/agent.toml"))]
    names = [s.name for s in specs]
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        raise ManifestError(f"duplicate agent names: {', '.join(sorted(dupes))}")
    return specs
