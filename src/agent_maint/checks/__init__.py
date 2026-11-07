"""Built-in maintenance checks. Each check is a callable (agent, ctx) -> list[Finding]."""

from .config_lint import check_config
from .eval_regression import check_evals
from .model_lifecycle import check_model_lifecycle
from .prompt_drift import check_prompt_drift, prompt_hash
from .tool_schema import check_tool_schemas

ALL_CHECKS = {
    "model_lifecycle": check_model_lifecycle,
    "prompt_drift": check_prompt_drift,
    "config_lint": check_config,
    "tool_schema": check_tool_schemas,
    "eval_regression": check_evals,
}

__all__ = ["ALL_CHECKS", "prompt_hash"]
