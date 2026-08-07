"""Agno adapter for orchestrating the budget agent."""

import logging
from typing import Any, Dict, Optional, TypedDict

from .agents import generate_budget

logger = logging.getLogger(__name__)


class BudgetState(TypedDict):
    text: str
    generated: Optional[Dict[str, Any]]


def _generate_node(state: BudgetState) -> BudgetState:
    logger.info("Budget Agno pipeline step starting: generate")
    generated = generate_budget(state["text"])
    logger.info("Budget Agno pipeline step completed: generate generated_keys=%s", sorted(generated.keys()))
    return {**state, "generated": generated}


def run_budget_pipeline_agno(document_text: str) -> Dict[str, Any]:
    logger.info("Budget Agno pipeline starting text_chars=%s", len(document_text or ""))
    state: BudgetState = {"text": document_text, "generated": None}
    result = _generate_node(state)
    generated = result.get("generated") or {}
    logger.info("Budget Agno pipeline completed generated_keys=%s", sorted(generated.keys()))
    return generated

