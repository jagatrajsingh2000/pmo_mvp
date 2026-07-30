"""Agents for the planner pipeline.

This module implements three logical agents:
- extractor: (handled in the API layer) extracts text from uploaded documents
- generator: creates timeline artifacts from the text
- reviewer: reviews generated artifacts and suggests improvements

The implementation uses `planner_agent.azure_client.call_azure_openai`.
If you want to plug in `langraph` later, this module is the place to adapt.
"""

from typing import Any, Dict, Tuple
from .azure_client import call_azure_openai


def agent_generator(document_text: str) -> Dict[str, Any]:
    prompt = (
        "You are a project timeline planner. Given the following project document content, "
        "extract and produce a JSON object with the following keys: wbs, project_schedule, "
        "sprint_plan, milestone_plan, critical_path, dependency_map, resource_allocation, "
        "timeline_risks, effort_estimation, schedule_optimizations. Use arrays or simple objects. "
        "Return only valid JSON. If a field cannot be determined, set it to null or an empty array.\n\n"
        f"Document content:\n\n{document_text[:8000]}"
    )
    return call_azure_openai(prompt)


def agent_reviewer(document_text: str, generated: Any) -> Dict[str, Any]:
    import json

    gen_text = generated if isinstance(generated, str) else json.dumps(generated, ensure_ascii=False)
    prompt = (
        "You are a senior project manager reviewing the generated project timeline outputs. "
        "Given the original project document content and the generated outputs, produce a short JSON object with: "
        "- issues: list of problems or missing information, "
        "- suggestions: list of concrete improvements or data to collect, "
        "- confidence: low/medium/high.\n\n"
        f"Original document snippet:\n{document_text[:3000]}\n\n"
        f"Generated outputs:\n{gen_text}"
    )
    return call_azure_openai(prompt)


def run_pipeline(document_text: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Run generator and reviewer in sequence and return (generated, review)."""
    generated = agent_generator(document_text)
    review = agent_reviewer(document_text, generated)
    return generated, review
