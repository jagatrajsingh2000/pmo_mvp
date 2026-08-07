"""Agno adapter for orchestrating the executive report agent."""

import logging
from typing import Any, Dict, Optional, TypedDict

from .agents import generate_executive_report

logger = logging.getLogger(__name__)


class ExecutiveState(TypedDict):
    text: str
    generated: Optional[Dict[str, Any]]


def _generate_node(state: ExecutiveState) -> ExecutiveState:
    logger.info("Executive Agno pipeline step starting: generate")
    generated = generate_executive_report(state["text"])
    logger.info("Executive Agno pipeline step completed: generate generated_keys=%s", sorted(generated.keys()))
    return {**state, "generated": generated}


def run_executive_pipeline_agno(source_bundle_text: str) -> Dict[str, Any]:
    logger.info("Executive Agno pipeline starting text_chars=%s", len(source_bundle_text or ""))
    state: ExecutiveState = {"text": source_bundle_text, "generated": None}
    result = _generate_node(state)
    generated = result.get("generated") or {}
    logger.info("Executive Agno pipeline completed generated_keys=%s", sorted(generated.keys()))
    return generated
