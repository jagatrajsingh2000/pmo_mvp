"""Agno adapter for orchestrating the BRD agent."""

import logging
from typing import Any, Dict, Optional, TypedDict

from .agents import generate_brd_preview

logger = logging.getLogger(__name__)


class BrdState(TypedDict):
    text: str
    filename: str
    generated: Optional[Dict[str, Any]]


def _generate_node(state: BrdState) -> BrdState:
    logger.info("BRD Agno pipeline step starting: generate")
    generated = generate_brd_preview(state["text"], state["filename"])
    logger.info("BRD Agno pipeline step completed: generate generated_keys=%s", sorted(generated.keys()))
    return {**state, "generated": generated}


def run_brd_pipeline_agno(document_text: str, filename: str = "workflow-brd.docx") -> Dict[str, Any]:
    logger.info("BRD Agno pipeline starting text_chars=%s", len(document_text or ""))
    state: BrdState = {"text": document_text, "filename": filename, "generated": None}
    result = _generate_node(state)
    generated = result.get("generated") or {}
    logger.info("BRD Agno pipeline completed generated_keys=%s", sorted(generated.keys()))
    return generated

