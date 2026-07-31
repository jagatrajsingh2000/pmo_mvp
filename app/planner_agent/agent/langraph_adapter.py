"""LangGraph adapter for orchestrating planner agents."""

from typing import Any, Dict, Optional, Tuple, TypedDict
import logging

try:
    from langgraph.graph import END, START, StateGraph

    LANGGRAPH_AVAILABLE = True
except Exception:
    END = START = StateGraph = None
    LANGGRAPH_AVAILABLE = False

from .agents import agent_generator, agent_reviewer

logger = logging.getLogger(__name__)


class PlannerState(TypedDict):
    text: str
    generated: Optional[Dict[str, Any]]
    review: Optional[Dict[str, Any]]


def _generate_node(state: PlannerState) -> PlannerState:
    logger.info("LangGraph node starting: generate")
    generated = agent_generator(state["text"])
    logger.info("LangGraph node completed: generate generated_keys=%s", sorted(generated.keys()))
    return {**state, "generated": generated}


def _review_node(state: PlannerState) -> PlannerState:
    logger.info("LangGraph node starting: review")
    generated = state.get("generated") or {}
    review = agent_reviewer(state["text"], generated)
    logger.info("LangGraph node completed: review review_keys=%s", sorted(review.keys()))
    return {**state, "review": review}


def _build_graph():
    graph = StateGraph(PlannerState)
    graph.add_node("generate", _generate_node)
    graph.add_node("review", _review_node)
    graph.add_edge(START, "generate")
    graph.add_edge("generate", "review")
    graph.add_edge("review", END)
    return graph.compile()


def run_pipeline_langraph(document_text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Run the planner pipeline using LangGraph.

    Returns (generated, review)
    """
    if not LANGGRAPH_AVAILABLE:
        raise RuntimeError("LangGraph is not installed. Install backend requirements before running the planner.")

    logger.info("LangGraph pipeline starting text_chars=%s", len(document_text))
    result = _build_graph().invoke({"text": document_text, "generated": None, "review": None})
    generated = result.get("generated") or {}
    review = result.get("review") or {}
    logger.info(
        "LangGraph pipeline completed generated_keys=%s review_keys=%s",
        sorted(generated.keys()),
        sorted(review.keys()),
    )
    return generated, review
