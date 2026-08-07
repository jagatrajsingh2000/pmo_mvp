import json
from typing import Any

from app.common.agent_runtime import document_context, to_json_text

USER_STORY_REQUIRED_KEYS = (
    "project_name",
    "summary",
    "epics",
    "backlog",
    "acceptance_criteria",
    "traceability",
    "quality_notes",
)

USER_STORY_JSON_CONTRACT = {
    "project_name": "string",
    "summary": "string",
    "epics": [
        {
            "epic_id": "EPIC-01",
            "name": "string",
            "business_value": "string",
            "priority": "Must Have | Should Have | Could Have",
        }
    ],
    "backlog": [
        {
            "story_id": "US-001",
            "epic_id": "EPIC-01",
            "title": "string",
            "as_a": "persona or role",
            "i_want": "capability",
            "so_that": "business/user outcome",
            "priority": "Must Have | Should Have | Could Have",
            "estimate_points": 1,
            "dependencies": ["US-000"],
            "acceptance_criteria": ["Given/When/Then or testable criterion"],
            "source_reference": "source BRD section/table/evidence",
        }
    ],
    "acceptance_criteria": [
        {
            "story_id": "US-001",
            "criteria": ["string"],
            "test_type": "Functional | Integration | Security | Performance | UAT",
        }
    ],
    "traceability": [
        {
            "source_requirement": "FR-001 or source section",
            "story_ids": ["US-001"],
            "evidence": "short quote or paraphrase",
            "confidence": "low | medium | high",
        }
    ],
    "quality_notes": {
        "coverage_summary": "string",
        "missing_or_ambiguous_requirements": ["string"],
        "recommendations": ["string"],
    },
}


def user_story_prompt(document_text: str) -> str:
    context = document_context(document_text, 22000)
    return (
        "You are the User Story Agent in a PMO workflow. "
        "Transform the BRD into a detailed product backlog with epics, user stories, acceptance criteria, estimates, dependencies, and traceability. "
        "Return exactly one valid JSON object and nothing else. Never use markdown or code fences. "
        "Use only information grounded in the source BRD. Preserve requirement IDs when available. "
        "Create enough backlog rows to cover all functional requirements, key non-functional requirements, integrations, reporting, security, admin, testing, and rollout work. "
        "If the BRD has many requirements, produce at least 10 to 20 user stories instead of compressing them into a few broad stories. "
        "The response must match this JSON shape and include every top-level key:\n"
        f"{json.dumps(USER_STORY_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"BRD content:\n{context}"
    )


def user_story_repair_prompt(document_text: str, invalid_response: Any, error: str) -> str:
    context = document_context(document_text, 22000)
    return (
        "Your previous User Story Agent response failed JSON/schema validation. "
        f"Validation error: {error}\n\n"
        "Return a corrected response as exactly one valid JSON object and nothing else. "
        "Include project_name, summary, epics, backlog, acceptance_criteria, traceability, and quality_notes. "
        "Do not use markdown or prose outside JSON. Expand the backlog if it is too shallow for the BRD.\n\n"
        f"Required JSON shape:\n{json.dumps(USER_STORY_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Previous invalid response:\n{to_json_text(invalid_response, 3500)}\n\n"
        f"BRD content:\n{context}"
    )

