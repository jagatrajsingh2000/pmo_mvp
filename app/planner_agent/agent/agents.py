from typing import Any, Dict, Tuple
import logging

from .azure_client import AIJsonParseError, call_agno_azure_openai, has_azure_config
from .prompts import ARTIFACT_KEYS, generator_prompt, generator_retry_prompt, reviewer_prompt

logger = logging.getLogger(__name__)


SUPPLEMENTAL_KEYS = ("source_traceability", "stakeholder_mapping", "requirements_quality", "audit_readiness")


def _expected_minimum_tasks(document_text: str) -> int:
    lowered = (document_text or "").lower()
    section_hits = sum(
        1
        for keyword in (
            "scope",
            "stakeholder",
            "functional requirement",
            "non-functional requirement",
            "integration",
            "dependencies",
            "risk",
            "acceptance criteria",
            "testing",
            "rollout",
            "governance",
            "sign-off",
            "gate",
        )
        if keyword in lowered
    )
    if len(document_text or "") > 6000 or section_hits >= 5:
        return 8
    if len(document_text or "") > 2500 or section_hits >= 3:
        return 6
    return 3


def _validate_generated(generated: Dict[str, Any], document_text: str = "") -> None:
    if not isinstance(generated, dict):
        raise RuntimeError("Azure OpenAI response must be a JSON object.")
    missing = [key for key in ARTIFACT_KEYS if key not in generated]
    if missing:
        raise RuntimeError(
            "Azure OpenAI response did not include required planner artifact keys: "
            + ", ".join(missing)
        )
    supplemental_missing = [key for key in SUPPLEMENTAL_KEYS if key not in generated]
    if supplemental_missing:
        raise RuntimeError(
            "Azure OpenAI response did not include required quality support keys: "
            + ", ".join(supplemental_missing)
        )
    min_tasks = _expected_minimum_tasks(document_text)
    wbs = generated.get("wbs")
    schedule = generated.get("project_schedule")
    if not isinstance(wbs, list):
        raise RuntimeError("Azure OpenAI response wbs must be an array.")
    if not isinstance(schedule, list):
        raise RuntimeError("Azure OpenAI response project_schedule must be an array.")
    if len(wbs) < min_tasks:
        raise RuntimeError(
            f"Azure OpenAI response is too shallow: wbs has {len(wbs)} rows, expected at least {min_tasks} "
            "for this BRD. Expand WBS from requirements, integrations, dependencies, testing, rollout, governance, and compliance sections."
        )
    if len(schedule) < min_tasks:
        raise RuntimeError(
            f"Azure OpenAI response is too shallow: project_schedule has {len(schedule)} rows, expected at least {min_tasks} "
            "with tasks aligned to the WBS."
        )
    if min_tasks >= 6:
        traceability = generated.get("source_traceability")
        if not isinstance(traceability, list) or len(traceability) < 4:
            raise RuntimeError("Azure OpenAI response needs at least 4 source_traceability rows for this BRD.")


def _validate_review(review: Dict[str, Any]) -> None:
    if not isinstance(review, dict):
        raise RuntimeError("Azure OpenAI reviewer response must be a JSON object.")
    missing = [key for key in ("issues", "suggestions", "confidence", "quality_scores", "overall_quality_score") if key not in review]
    if missing:
        raise RuntimeError("Azure OpenAI reviewer response missing keys: " + ", ".join(missing))
    if not isinstance(review.get("quality_scores"), list):
        raise RuntimeError("Azure OpenAI reviewer quality_scores must be an array.")


def _generate_with_ai(document_text: str) -> Dict[str, Any]:
    first_response = None
    try:
        first_response = call_agno_azure_openai(generator_prompt(document_text), max_tokens=12000, request_label="generator")
        _validate_generated(first_response, document_text)
        return first_response
    except Exception as first_error:
        raw_response = first_error.raw_text if isinstance(first_error, AIJsonParseError) else first_response
        logger.warning("Generator response failed validation; retrying with repair prompt: %s", first_error)
        repaired = call_agno_azure_openai(
            generator_retry_prompt(document_text, raw_response or "", str(first_error)),
            max_tokens=12000,
            request_label="generator_retry",
        )
        _validate_generated(repaired, document_text)
        return repaired


def agent_generator(document_text: str) -> Dict[str, Any]:
    logger.info("Planner generator starting text_chars=%s", len(document_text))
    if not has_azure_config():
        raise RuntimeError("Azure OpenAI is not configured. Set the required Azure OpenAI environment variables.")
    generated = _generate_with_ai(document_text)
    logger.info("Planner generator completed via Azure OpenAI")
    return generated


def agent_reviewer(document_text: str, generated: Any) -> Dict[str, Any]:
    logger.info("Planner reviewer starting")
    if not has_azure_config():
        raise RuntimeError("Azure OpenAI is not configured. Set the required Azure OpenAI environment variables.")
    review = call_agno_azure_openai(reviewer_prompt(document_text, generated), max_tokens=6000, request_label="reviewer")
    _validate_review(review)
    logger.info("Planner reviewer completed via Azure OpenAI")
    return review


def run_pipeline(document_text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Run generator and reviewer in sequence and return (generated, review)."""
    generated = agent_generator(document_text)
    review = agent_reviewer(document_text, generated)
    return generated, review
