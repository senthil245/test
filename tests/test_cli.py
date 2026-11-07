import json

from agent_maint.cli import main
from agent_maint.registry import discover

from conftest import write_results


def test_check_json_and_exit_code(repo, capsys):
    assert main(["--repo", str(repo), "check", "--format", "json", "--today", "2026-11-07"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert {a["name"] for a in data["agents"]} == {"support-triage", "data-quality"}

    write_results(repo, "data-quality", f1=0.5, false_positive_rate=0.04)
    assert main(["--repo", str(repo), "check", "--today", "2026-11-07"]) == 1
    assert main(["--repo", str(repo), "check", "--fail-on", "never"]) == 0


def test_markdown_report_written(repo):
    out = repo / "reports" / "r.md"
    main(["--repo", str(repo), "check", "--format", "markdown", "--output", str(out)])
    text = out.read_text()
    assert text.startswith("# Agent maintenance report") and "support-triage" in text


def test_lock_repins_after_prompt_edit(repo):
    a = next(a for a in discover(repo / "agents") if a.name == "support-triage")
    a.prompt_path.write_text("New prompt.\n")
    assert main(["--repo", str(repo), "check", "--only", "prompt_drift"]) == 1
    assert main(["--repo", str(repo), "lock"]) == 0
    assert main(["--repo", str(repo), "check", "--only", "prompt_drift"]) == 0


def test_bad_manifest_exit_2(repo):
    (repo / "agents" / "broken").mkdir()
    (repo / "agents" / "broken" / "agent.toml").write_text("[agent]\nname = 'broken'\n")
    assert main(["--repo", str(repo), "list"]) == 2
