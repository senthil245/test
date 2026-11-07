"""Detect prompt edits that bypassed review (hash in manifest != file on disk)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ..context import RunContext
from ..models import AgentSpec, Finding, Severity

NAME = "prompt_drift"


def prompt_hash(path: Path) -> str:
    # Normalise line endings so Windows checkouts don't register as drift.
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def check_prompt_drift(agent: AgentSpec, ctx: RunContext) -> list[Finding]:
    if not agent.prompt_path.exists():
        return [Finding(NAME, agent.name, Severity.ERROR,
                        f"prompt file not found: {agent.prompt_path.relative_to(ctx.repo_root)}",
                        "Create the prompt file or fix [agent].prompt_file.")]
    if not agent.prompt_sha256:
        return [Finding(NAME, agent.name, Severity.WARN,
                        "no prompt_sha256 pinned in manifest",
                        "Run `agent-maint lock` to pin the current prompt.")]
    actual = prompt_hash(agent.prompt_path)
    if actual != agent.prompt_sha256:
        return [Finding(NAME, agent.name, Severity.ERROR,
                        f"prompt changed without re-locking (expected {agent.prompt_sha256[:12]}, got {actual[:12]})",
                        "Re-run evals, then `agent-maint lock` and commit the new hash with the prompt change.")]
    return []
