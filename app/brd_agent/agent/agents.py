import logging
from typing import Any, Dict

from app.common.agent_runtime import generate_required_json

from .prompts import BRD_REQUIRED_KEYS, brd_prompt, brd_repair_prompt

logger = logging.getLogger(__name__)


def _validate_brd(payload: Dict[str, Any]) -> None:
    resolved = payload.get("resolved")
    if not isinstance(resolved, dict):
        raise RuntimeError("BRD Agent response resolved must be an object.")
    required_sections = (
        "project_details",
        "executive_summary",
        "scope",
        "stakeholders",
        "functional_requirements",
        "non_functional_requirements",
        "integrations",
        "dependencies",
        "raid",
        "governance_signoff",
    )
    missing = [section for section in required_sections if section not in resolved]
    if missing:
        raise RuntimeError("BRD Agent resolved object missing sections: " + ", ".join(missing))


def generate_brd_preview(document_text: str, filename: str = "workflow-brd.docx") -> Dict[str, Any]:
    logger.info("BRD agent starting text_chars=%s filename=%s", len(document_text or ""), filename)
    result = generate_required_json(
        agent_name="brd_agent",
        prompt=brd_prompt(document_text, filename),
        required_keys=BRD_REQUIRED_KEYS,
        repair_prompt=lambda invalid, error: brd_repair_prompt(document_text, invalid, error, filename),
        validator=_validate_brd,
        max_tokens=14000,
    )
    logger.info("BRD agent completed demand_id=%s resolved_sections=%s", result.get("demand_id"), sorted(result["resolved"].keys()))
    return result
