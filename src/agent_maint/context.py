"""Shared run context passed to every check."""

from __future__ import annotations

import datetime as dt
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RunContext:
    repo_root: Path
    today: dt.date = field(default_factory=dt.date.today)
    lifecycle: dict[str, Any] = field(default_factory=dict)
    warn_days_before_retirement: int = 60

    @property
    def baselines_dir(self) -> Path:
        return self.repo_root / "evals" / "baselines"

    @property
    def results_dir(self) -> Path:
        return self.repo_root / "evals" / "results"

    @classmethod
    def from_repo(cls, repo_root: Path, today: dt.date | None = None) -> "RunContext":
        lifecycle_path = repo_root / "config" / "model_lifecycle.toml"
        lifecycle: dict[str, Any] = {}
        warn_days = 60
        if lifecycle_path.exists():
            data = tomllib.loads(lifecycle_path.read_text(encoding="utf-8"))
            lifecycle = data.get("models", {})
            warn_days = data.get("settings", {}).get("warn_days_before_retirement", 60)
        return cls(
            repo_root=repo_root,
            today=today or dt.date.today(),
            lifecycle=lifecycle,
            warn_days_before_retirement=warn_days,
        )
