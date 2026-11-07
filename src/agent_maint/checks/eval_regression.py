"""Compare the latest eval results against the committed baseline.

Files (JSON): evals/baselines/<agent>.json and evals/results/<agent>.json, each
    {"metrics": {"accuracy": 0.91, "p95_latency_s": 4.2, ...}}

The manifest's [evals] section declares tolerances:
    [evals]
    suite = "support-triage-v1"
    [evals.metrics.accuracy]
    direction = "higher"      # higher is better
    max_drop = 0.02           # absolute tolerance
    [evals.metrics.p95_latency_s]
    direction = "lower"
    max_increase = 0.5
"""

from __future__ import annotations

import json

from ..context import RunContext
from ..models import AgentSpec, Finding, Severity

NAME = "eval_regression"


def _load(path):
    return json.loads(path.read_text(encoding="utf-8")).get("metrics", {})


def check_evals(agent: AgentSpec, ctx: RunContext) -> list[Finding]:
    metrics_cfg = agent.evals.get("metrics", {})
    if not metrics_cfg:
        return []
    base_path = ctx.baselines_dir / f"{agent.name}.json"
    res_path = ctx.results_dir / f"{agent.name}.json"
    if not base_path.exists():
        return [Finding(NAME, agent.name, Severity.WARN, "no eval baseline committed",
                        f"Run the suite and save {base_path.relative_to(ctx.repo_root)}.")]
    if not res_path.exists():
        return [Finding(NAME, agent.name, Severity.INFO, "no fresh eval results to compare",
                        "Run the eval suite in CI to produce evals/results/.")]

    base, res = _load(base_path), _load(res_path)
    out: list[Finding] = []
    for metric, cfg in metrics_cfg.items():
        if metric not in base or metric not in res:
            out.append(Finding(NAME, agent.name, Severity.WARN, f"metric '{metric}' missing from baseline or results"))
            continue
        b, r = float(base[metric]), float(res[metric])
        if cfg.get("direction", "higher") == "higher":
            tol = float(cfg.get("max_drop", 0.0))
            if b - r > tol:
                out.append(Finding(NAME, agent.name, Severity.ERROR,
                                   f"{metric} regressed {b:.4g} -> {r:.4g} (drop {b - r:.4g} > {tol:.4g})",
                                   "Investigate the prompt/model change or update the baseline deliberately."))
        else:
            tol = float(cfg.get("max_increase", 0.0))
            if r - b > tol:
                out.append(Finding(NAME, agent.name, Severity.ERROR,
                                   f"{metric} regressed {b:.4g} -> {r:.4g} (increase {r - b:.4g} > {tol:.4g})",
                                   "Investigate the prompt/model change or update the baseline deliberately."))
    return out
