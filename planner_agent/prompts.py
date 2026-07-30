from typing import Any
import json

ARTIFACT_KEYS = [
    "wbs",
    "project_schedule",
    "sprint_plan",
    "milestone_plan",
    "critical_path",
    "dependency_map",
    "resource_allocation",
    "timeline_risks",
    "effort_estimation",
    "schedule_optimizations",
]


def generator_prompt(document_text: str) -> str:
    keys = ", ".join(ARTIFACT_KEYS)
    return (
        "You are a project timeline planner. Given the following project document content, "
        f"extract and produce a JSON object with these exact keys: {keys}. "
        "Use arrays or simple objects. Include task names, owners, dependencies, start dates, "
        "end dates, durations, and confidence where the document supports them. Return only valid JSON. "
        "If a field cannot be determined, set it to null or an empty array.\n\n"
        f"Document content:\n\n{document_text[:8000]}"
    )


def reviewer_prompt(document_text: str, generated: Any) -> str:
    gen_text = generated if isinstance(generated, str) else json.dumps(generated, ensure_ascii=False)
    return (
        "You are a senior project manager reviewing generated project timeline outputs. "
        "Given the original project document content and generated outputs, produce a short JSON object with: "
        "issues, suggestions, confidence.\n\n"
        f"Original document snippet:\n{document_text[:3000]}\n\n"
        f"Generated outputs:\n{gen_text}"
    )
