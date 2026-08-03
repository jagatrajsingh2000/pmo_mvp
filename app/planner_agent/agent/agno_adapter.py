"""Agno adapter for orchestrating planner agents."""

from typing import Any, Dict, Optional, Tuple, TypedDict
import logging

from .agents import agent_generator, agent_reviewer

logger = logging.getLogger(__name__)


class PlannerState(TypedDict):
    text: str
    generated: Optional[Dict[str, Any]]
    review: Optional[Dict[str, Any]]


def _generate_node(state: PlannerState) -> PlannerState:
    logger.info("Agno pipeline step starting: generate")
    generated = agent_generator(state["text"])
    logger.info("Agno pipeline step completed: generate generated_keys=%s", sorted(generated.keys()))
    return {**state, "generated": generated}


def _review_node(state: PlannerState) -> PlannerState:
    logger.info("Agno pipeline step starting: review")
    generated = state.get("generated") or {}
    review = agent_reviewer(state["text"], generated)
    logger.info("Agno pipeline step completed: review review_keys=%s", sorted(review.keys()))
    return {**state, "review": review}


def run_pipeline_agno(document_text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Run the planner pipeline using Agno-backed agents.

    Returns (generated, review)
    """
    logger.info("Agno pipeline starting text_chars=%s", len(document_text))
    state: PlannerState = {"text": document_text, "generated": None, "review": None}
    result = _review_node(_generate_node(state))
    generated = result.get("generated") or {}
    review = result.get("review") or {}
    logger.info(
        "Agno pipeline completed generated_keys=%s review_keys=%s",
        sorted(generated.keys()),
        sorted(review.keys()),
    )
    return generated, review
