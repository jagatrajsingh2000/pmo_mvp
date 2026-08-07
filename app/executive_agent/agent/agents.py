import logging
from typing import Any, Dict

from app.common.agent_runtime import generate_required_json

from .prompts import EXECUTIVE_REQUIRED_KEYS, executive_prompt, executive_repair_prompt

logger = logging.getLogger(__name__)


def _validate_executive_report(payload: Dict[str, Any]) -> None:
    if not isinstance(payload.get("portfolio_health"), dict):
        raise RuntimeError("Executive Report Agent response portfolio_health must be an object.")
    if not isinstance(payload.get("top_risks"), list):
        raise RuntimeError("Executive Report Agent response top_risks must be an array.")
    if not isinstance(payload.get("recommendations"), list):
        raise RuntimeError("Executive Report Agent response recommendations must be an array.")


def generate_executive_report(source_bundle_text: str) -> Dict[str, Any]:
    logger.info("Executive Report agent starting text_chars=%s", len(source_bundle_text or ""))
    result = generate_required_json(
        agent_name="executive_report_agent",
        prompt=executive_prompt(source_bundle_text),
        required_keys=EXECUTIVE_REQUIRED_KEYS,
        repair_prompt=lambda invalid, error: executive_repair_prompt(source_bundle_text, invalid, error),
        validator=_validate_executive_report,
        max_tokens=12000,
    )
    logger.info("Executive Report agent completed status=%s risks=%s", result.get("portfolio_health", {}).get("overall_status"), len(result.get("top_risks", [])))
    return result
