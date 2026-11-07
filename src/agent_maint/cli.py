"""Command-line entry point: `agent-maint list|check|lock`."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

from .checks import ALL_CHECKS, prompt_hash
from .context import RunContext
from .models import Severity
from .registry import ManifestError, discover
from .report import RENDERERS
from .runner import run, worst

FAIL_ON = {"error": Severity.ERROR, "warn": Severity.WARN, "never": None}


def _lock(repo: Path) -> int:
    """Pin each agent's current prompt hash into its manifest."""
    changed = 0
    for agent in discover(repo / "agents"):
        if not agent.prompt_path.exists():
            print(f"skip {agent.name}: prompt file missing", file=sys.stderr)
            continue
        digest = prompt_hash(agent.prompt_path)
        if digest == agent.prompt_sha256:
            continue
        text = agent.manifest_path.read_text(encoding="utf-8")
        line = f'prompt_sha256 = "{digest}"'
        if re.search(r"^prompt_sha256\s*=.*$", text, flags=re.M):
            text = re.sub(r"^prompt_sha256\s*=.*$", line, text, count=1, flags=re.M)
        else:
            text = re.sub(r"^\[agent\]\s*$", f"[agent]\n{line}", text, count=1, flags=re.M)
        agent.manifest_path.write_text(text, encoding="utf-8")
        print(f"locked {agent.name}: {digest[:12]}")
        changed += 1
    print(f"{changed} manifest(s) updated")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="agent-maint", description=__doc__)
    p.add_argument("--repo", type=Path, default=Path.cwd(), help="repository root (default: cwd)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="list registered agents")
    sub.add_parser("lock", help="pin current prompt hashes into manifests")

    c = sub.add_parser("check", help="run maintenance checks")
    c.add_argument("--only", action="append", choices=sorted(ALL_CHECKS), help="run only these checks")
    c.add_argument("--format", choices=sorted(RENDERERS), default="text")
    c.add_argument("--output", type=Path, help="write report to file instead of stdout")
    c.add_argument("--fail-on", choices=sorted(FAIL_ON), default="error",
                   help="exit non-zero at this severity (default: error)")
    c.add_argument("--today", type=dt.date.fromisoformat, help="override today's date (YYYY-MM-DD)")

    args = p.parse_args(argv)
    repo = args.repo.resolve()
    try:
        if args.cmd == "lock":
            return _lock(repo)
        agents = discover(repo / "agents")
        if args.cmd == "list":
            for a in agents:
                print(f"{a.name:<20} {a.model:<28} {a.owner}")
            return 0

        ctx = RunContext.from_repo(repo, today=args.today)
        findings = run(agents, ctx, only=args.only)
        report = RENDERERS[args.format](agents, findings)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(report, encoding="utf-8")
        else:
            print(report)
        threshold = FAIL_ON[args.fail_on]
        return 1 if threshold is not None and worst(findings) >= threshold else 0
    except ManifestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
