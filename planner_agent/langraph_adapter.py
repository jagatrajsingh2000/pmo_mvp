"""LangGraph adapter for orchestrating planner agents."""

from typing import Any, Dict, Optional, Tuple, TypedDict
import logging

try:
    from langgraph.graph import END, START, StateGraph

    LANGGRAPH_AVAILABLE = True
except Exception:
    END = START = StateGraph = None
    LANGGRAPH_AVAILABLE = False

from .agents import agent_generator, agent_reviewer, run_pipeline

logger = logging.getLogger(__name__)


class PlannerState(TypedDict):
    text: str
    generated: Optional[Dict[str, Any]]
    review: Optional[Dict[str, Any]]


def _generate_node(state: PlannerState) -> PlannerState:
    generated = agent_generator(state["text"])
    return {**state, "generated": generated}


def _review_node(state: PlannerState) -> PlannerState:
    generated = state.get("generated") or {}
    review = agent_reviewer(state["text"], generated)
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
    """Run the planner pipeline using LangGraph if available, else fallback.

    Returns (generated, review)
    """
    if not LANGGRAPH_AVAILABLE:
        logger.info("LangGraph not available; falling back to local pipeline")
        return run_pipeline(document_text)

    try:
        result = _build_graph().invoke({"text": document_text, "generated": None, "review": None})
        return result.get("generated") or {}, result.get("review") or {}
    except Exception as e:
        logger.exception("LangGraph execution failed; running sequential pipeline: %s", e)
        return run_pipeline(document_text)
