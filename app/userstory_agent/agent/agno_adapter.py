"""Agno adapter for orchestrating the user story agent."""

import logging
from typing import Any, Dict, Optional, TypedDict

from .agents import generate_user_stories

logger = logging.getLogger(__name__)


class UserStoryState(TypedDict):
    text: str
    generated: Optional[Dict[str, Any]]


def _generate_node(state: UserStoryState) -> UserStoryState:
    logger.info("User Story Agno pipeline step starting: generate")
    generated = generate_user_stories(state["text"])
    logger.info("User Story Agno pipeline step completed: generate generated_keys=%s", sorted(generated.keys()))
    return {**state, "generated": generated}


def run_userstory_pipeline_agno(document_text: str) -> Dict[str, Any]:
    logger.info("User Story Agno pipeline starting text_chars=%s", len(document_text or ""))
    state: UserStoryState = {"text": document_text, "generated": None}
    result = _generate_node(state)
    generated = result.get("generated") or {}
    logger.info("User Story Agno pipeline completed generated_keys=%s", sorted(generated.keys()))
    return generated

