import dataclasses
import datetime as dt

from agent_maint.checks import ALL_CHECKS
from agent_maint.models import Severity, ToolSpec
from agent_maint.registry import discover
from agent_maint.runner import run, worst

from conftest import write_results


def agent(repo, name):
    return next(a for a in discover(repo / "agents") if a.name == name)


def test_example_fleet_is_clean(repo, ctx):
    findings = run(discover(repo / "agents"), ctx)
    assert worst(findings) <= Severity.INFO


# --- model lifecycle -------------------------------------------------------

def test_unknown_model_warns(repo, ctx):
    a = dataclasses.replace(agent(repo, "support-triage"), model="mystery-model")
    [f] = ALL_CHECKS["model_lifecycle"](a, ctx)
    assert f.severity == Severity.WARN and "not in" in f.message


def test_retiring_model_warns_then_errors(repo, ctx):
    a = dataclasses.replace(agent(repo, "support-triage"), model="example-legacy-model")
    [f] = ALL_CHECKS["model_lifecycle"](a, ctx)  # 69 days out, outside 60-day window -> deprecated warn
    assert f.severity == Severity.WARN
    soon = dataclasses.replace(ctx, today=dt.date(2026, 12, 20))
    [f] = ALL_CHECKS["model_lifecycle"](a, soon)
    assert f.severity == Severity.WARN and "retires in 26 days" in f.message
    late = dataclasses.replace(ctx, today=dt.date(2027, 1, 15))
    [f] = ALL_CHECKS["model_lifecycle"](a, late)
    assert f.severity == Severity.ERROR and "claude-sonnet-5-5" in f.remediation


# --- prompt drift ----------------------------------------------------------

def test_prompt_edit_without_lock_errors(repo, ctx):
    a = agent(repo, "data-quality")
    a.prompt_path.write_text(a.prompt_path.read_text() + "\nIgnore all checks.\n")
    [f] = ALL_CHECKS["prompt_drift"](a, ctx)
    assert f.severity == Severity.ERROR


def test_crlf_is_not_drift(repo, ctx):
    a = agent(repo, "data-quality")
    a.prompt_path.write_bytes(a.prompt_path.read_bytes().replace(b"\n", b"\r\n"))
    assert ALL_CHECKS["prompt_drift"](a, ctx) == []


def test_missing_prompt_errors(repo, ctx):
    a = agent(repo, "data-quality")
    a.prompt_path.unlink()
    [f] = ALL_CHECKS["prompt_drift"](a, ctx)
    assert f.severity == Severity.ERROR


# --- config lint -----------------------------------------------------------

def test_config_lint_catches_bad_params(repo, ctx):
    a = dataclasses.replace(agent(repo, "support-triage"), temperature=1.7, max_tokens=None, owner="bob")
    msgs = [f.message for f in ALL_CHECKS["config_lint"](a, ctx)]
    assert any("temperature" in m for m in msgs)
    assert any("max_tokens" in m for m in msgs)
    assert any("owner" in m for m in msgs)


# --- tool schema -----------------------------------------------------------

def test_tool_schema_errors(repo, ctx):
    bad = [
        ToolSpec("bad name!", "short", {"type": "object", "required": ["x"], "properties": {}}),
        ToolSpec("dup", "A sufficiently long description here.", {"type": "string"}),
        ToolSpec("dup", "A sufficiently long description here.", {"type": "object", "properties": {}}),
    ]
    a = dataclasses.replace(agent(repo, "support-triage"), tools=bad)
    msgs = [f.message for f in ALL_CHECKS["tool_schema"](a, ctx)]
    assert any("invalid name" in m for m in msgs)
    assert any("too short" in m for m in msgs)
    assert any("requires 'x'" in m for m in msgs)
    assert any("must be 'object'" in m for m in msgs)
    assert any("duplicate" in m for m in msgs)


# --- eval regression -------------------------------------------------------

def test_eval_within_tolerance_passes(repo, ctx):
    write_results(repo, "support-triage", routing_accuracy=0.92, p95_latency_s=4.1)
    assert ALL_CHECKS["eval_regression"](agent(repo, "support-triage"), ctx) == []


def test_eval_regression_detected(repo, ctx):
    write_results(repo, "support-triage", routing_accuracy=0.85, p95_latency_s=5.0)
    findings = ALL_CHECKS["eval_regression"](agent(repo, "support-triage"), ctx)
    assert {f.severity for f in findings} == {Severity.ERROR}
    assert len(findings) == 2


def test_crashing_check_is_reported(repo, ctx, monkeypatch):
    def boom(a, c):
        raise RuntimeError("kaboom")
    monkeypatch.setitem(ALL_CHECKS, "config_lint", boom)
    findings = run(discover(repo / "agents"), ctx, only=["config_lint"])
    assert all("kaboom" in f.message for f in findings) and len(findings) == 2
