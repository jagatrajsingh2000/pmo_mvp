from typing import Any, Dict, Tuple

from .azure_client import call_azure_openai, feature_fallback_enabled, has_azure_config
from .local_planner import create_plan, review_plan
from .prompts import generator_prompt, reviewer_prompt


def agent_generator(document_text: str) -> Dict[str, Any]:
    if not has_azure_config():
        if not feature_fallback_enabled():
            raise RuntimeError(
                "Azure OpenAI is not configured. Set Azure env variables or set FEATURE_FALLBACK=True."
            )
        return create_plan(document_text)
    try:
        return call_azure_openai(generator_prompt(document_text))
    except Exception as exc:
        if not feature_fallback_enabled():
            raise
        fallback = create_plan(document_text)
        fallback["planner_warning"] = f"Azure OpenAI failed; used local planner fallback: {exc}"
        return fallback


def agent_reviewer(document_text: str, generated: Any) -> Dict[str, Any]:
    if not has_azure_config():
        if not feature_fallback_enabled():
            raise RuntimeError(
                "Azure OpenAI is not configured. Set Azure env variables or set FEATURE_FALLBACK=True."
            )
        return review_plan(document_text, generated if isinstance(generated, dict) else {"text": generated})
    try:
        return call_azure_openai(reviewer_prompt(document_text, generated))
    except Exception as exc:
        if not feature_fallback_enabled():
            raise
        fallback = review_plan(document_text, generated if isinstance(generated, dict) else {"text": generated})
        fallback["review_warning"] = f"Azure OpenAI failed; used local review fallback: {exc}"
        return fallback


def run_pipeline(document_text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Run generator and reviewer in sequence and return (generated, review)."""
    generated = agent_generator(document_text)
    review = agent_reviewer(document_text, generated)
    return generated, review
