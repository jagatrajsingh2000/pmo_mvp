from typing import Any, Dict, Tuple
import logging

from .azure_client import AIJsonParseError, call_azure_openai, feature_fallback_enabled, has_azure_config
from .local_planner import create_plan, review_plan
from .prompts import ARTIFACT_KEYS, generator_prompt, generator_retry_prompt, reviewer_prompt

logger = logging.getLogger(__name__)


def _validate_generated(generated: Dict[str, Any]) -> None:
    if not isinstance(generated, dict):
        raise RuntimeError("Azure OpenAI response must be a JSON object.")
    missing = [key for key in ARTIFACT_KEYS if key not in generated]
    if missing:
        raise RuntimeError(
            "Azure OpenAI response did not include required planner artifact keys: "
            + ", ".join(missing)
        )


def _validate_review(review: Dict[str, Any]) -> None:
    if not isinstance(review, dict):
        raise RuntimeError("Azure OpenAI reviewer response must be a JSON object.")
    missing = [key for key in ("issues", "suggestions", "confidence") if key not in review]
    if missing:
        raise RuntimeError("Azure OpenAI reviewer response missing keys: " + ", ".join(missing))


def _generate_with_ai(document_text: str) -> Dict[str, Any]:
    first_response = None
    try:
        first_response = call_azure_openai(generator_prompt(document_text), request_label="generator")
        _validate_generated(first_response)
        return first_response
    except Exception as first_error:
        raw_response = first_error.raw_text if isinstance(first_error, AIJsonParseError) else first_response
        logger.warning("Generator response failed validation; retrying with repair prompt: %s", first_error)
        repaired = call_azure_openai(
            generator_retry_prompt(document_text, raw_response or "", str(first_error)),
            request_label="generator_retry",
        )
        _validate_generated(repaired)
        return repaired


def agent_generator(document_text: str) -> Dict[str, Any]:
    logger.info("Planner generator starting text_chars=%s", len(document_text))
    if not has_azure_config():
        if not feature_fallback_enabled():
            raise RuntimeError(
                "Azure OpenAI is not configured. Set Azure env variables or set FEATURE_FALLBACK=True."
            )
        logger.warning("FEATURE_FALLBACK=True; using local deterministic generator")
        generated = create_plan(document_text)
        logger.info("Planner generator completed via local fallback")
        return generated
    try:
        generated = _generate_with_ai(document_text)
        logger.info("Planner generator completed via Azure OpenAI")
        return generated
    except Exception as exc:
        if not feature_fallback_enabled():
            logger.exception("Planner generator failed and fallback is disabled")
            raise
        logger.exception("Planner generator failed; FEATURE_FALLBACK=True so local fallback will run")
        fallback = create_plan(document_text)
        fallback["planner_warning"] = f"Azure OpenAI failed; used local planner fallback: {exc}"
        return fallback


def agent_reviewer(document_text: str, generated: Any) -> Dict[str, Any]:
    logger.info("Planner reviewer starting")
    if not has_azure_config():
        if not feature_fallback_enabled():
            raise RuntimeError(
                "Azure OpenAI is not configured. Set Azure env variables or set FEATURE_FALLBACK=True."
            )
        logger.warning("FEATURE_FALLBACK=True; using local deterministic reviewer")
        review = review_plan(document_text, generated if isinstance(generated, dict) else {"text": generated})
        logger.info("Planner reviewer completed via local fallback")
        return review
    try:
        review = call_azure_openai(reviewer_prompt(document_text, generated), request_label="reviewer")
        _validate_review(review)
        logger.info("Planner reviewer completed via Azure OpenAI")
        return review
    except Exception as exc:
        if not feature_fallback_enabled():
            logger.exception("Planner reviewer failed and fallback is disabled")
            raise
        logger.exception("Planner reviewer failed; FEATURE_FALLBACK=True so local fallback will run")
        fallback = review_plan(document_text, generated if isinstance(generated, dict) else {"text": generated})
        fallback["review_warning"] = f"Azure OpenAI failed; used local review fallback: {exc}"
        return fallback


def run_pipeline(document_text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Run generator and reviewer in sequence and return (generated, review)."""
    generated = agent_generator(document_text)
    review = agent_reviewer(document_text, generated)
    return generated, review
