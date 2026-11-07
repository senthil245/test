import datetime as dt
import json
import shutil
from pathlib import Path

import pytest

from agent_maint.context import RunContext

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A throwaway copy of the example fleet that tests can mutate."""
    for d in ("agents", "config", "evals"):
        shutil.copytree(REPO / d, tmp_path / d)
    return tmp_path


@pytest.fixture
def ctx(repo: Path) -> RunContext:
    return RunContext.from_repo(repo, today=dt.date(2026, 11, 7))


def write_results(repo: Path, agent: str, **metrics):
    (repo / "evals" / "results" / f"{agent}.json").write_text(json.dumps({"metrics": metrics}))
