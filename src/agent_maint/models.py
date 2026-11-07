"""Core data types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any


class Severity(IntEnum):
    OK = 0
    INFO = 1
    WARN = 2
    ERROR = 3

    @property
    def label(self) -> str:
        return self.name.lower()


@dataclass
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass
class AgentSpec:
    """An agent as declared in agents/<name>/agent.toml."""

    name: str
    owner: str
    model: str
    root: Path
    prompt_file: str = "prompt.md"
    prompt_sha256: str | None = None
    max_tokens: int | None = None
    temperature: float | None = None
    tools: list[ToolSpec] = field(default_factory=list)
    evals: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def manifest_path(self) -> Path:
        return self.root / "agent.toml"

    @property
    def prompt_path(self) -> Path:
        return self.root / self.prompt_file


@dataclass
class Finding:
    check: str
    agent: str
    severity: Severity
    message: str
    remediation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "agent": self.agent,
            "severity": self.severity.label,
            "message": self.message,
            "remediation": self.remediation,
        }
