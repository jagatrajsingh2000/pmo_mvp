import logging
from typing import Any, Dict

from app.common.agent_runtime import generate_required_json

from .prompts import BUDGET_REQUIRED_KEYS, budget_prompt, budget_repair_prompt

logger = logging.getLogger(__name__)


def _validate_budget(payload: Dict[str, Any]) -> None:
    if not isinstance(payload.get("workstream_estimates"), list):
        raise RuntimeError("Budget Agent response workstream_estimates must be an array.")
    if not isinstance(payload.get("resource_costs"), list):
        raise RuntimeError("Budget Agent response resource_costs must be an array.")
    if not isinstance(payload.get("cost_summary"), dict):
        raise RuntimeError("Budget Agent response cost_summary must be an object.")


def generate_budget(document_text: str) -> Dict[str, Any]:
    logger.info("Budget agent starting text_chars=%s", len(document_text or ""))
    result = generate_required_json(
        agent_name="budget_agent",
        prompt=budget_prompt(document_text),
        required_keys=BUDGET_REQUIRED_KEYS,
        repair_prompt=lambda invalid, error: budget_repair_prompt(document_text, invalid, error),
        validator=_validate_budget,
        max_tokens=12000,
    )
    logger.info("Budget agent completed workstreams=%s resources=%s", len(result.get("workstream_estimates", [])), len(result.get("resource_costs", [])))
    return result
