.PHONY: install test check lock report

install:
	pip install -e ".[dev]"

test:
	pytest -q

check:
	agent-maint check

lock:
	agent-maint lock

report:
	agent-maint check --format markdown --output reports/maintenance-report.md || true
