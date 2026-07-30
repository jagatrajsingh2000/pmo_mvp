"""Optional Langraph adapter for orchestrating planner agents.

This adapter tries to use `langraph` if it's installed. If not available, it falls back
to the local `run_pipeline` implementation from `planner_agent.agents`.

To enable full Langraph integration, install the `langraph` package and adapt the
`build_graph` function below to match the Langraph API you want to use.
"""

from typing import Any, Dict, Tuple
import logging

try:
    import langraph  # type: ignore
    LANGRAPH_AVAILABLE = True
except Exception:
    LANGRAPH_AVAILABLE = False

from .agents import run_pipeline

logger = logging.getLogger(__name__)


def run_pipeline_langraph(document_text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Run the planner pipeline using Langraph if available, else fallback.

    Returns (generated, review)
    """
    if not LANGRAPH_AVAILABLE:
        logger.info("Langraph not available; falling back to local pipeline")
        return run_pipeline(document_text)

    # If Langraph is installed, attempt a basic graph orchestration. The exact
    # API depends on the langraph package version; users should adapt this.
    try:
        # Example pseudo-code: build and execute a graph with two nodes.
        # Replace this with actual Langraph usage if needed.
        graph = langraph.Graph(name="planner_pipeline")

        def gen_node(ctx):
            ctx["generated"] = run_pipeline(ctx["text"])[0]

        def review_node(ctx):
            ctx["review"] = run_pipeline(ctx["text"])[1]

        graph.add_node("generate", gen_node)
        graph.add_node("review", review_node, depends_on=["generate"])

        ctx = {"text": document_text}
        graph.run(ctx)

        generated = ctx.get("generated")
        review = ctx.get("review")
        return generated, review
    except Exception as e:
        logger.exception("Langraph execution failed, falling back: %s", e)
        return run_pipeline(document_text)
