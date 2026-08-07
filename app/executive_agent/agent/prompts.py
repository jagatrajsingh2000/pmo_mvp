import json
from typing import Any

from app.common.agent_runtime import document_context, to_json_text

EXECUTIVE_REQUIRED_KEYS = (
    "project_name",
    "executive_summary",
    "portfolio_health",
    "key_metrics",
    "timeline_summary",
    "budget_summary",
    "top_risks",
    "decisions_required",
    "recommendations",
    "next_steps",
    "traceability",
)

EXECUTIVE_JSON_CONTRACT = {
    "project_name": "string",
    "executive_summary": "string",
    "portfolio_health": {
        "overall_status": "Green | Amber | Red",
        "schedule_status": "Green | Amber | Red",
        "budget_status": "Green | Amber | Red",
        "scope_status": "Green | Amber | Red",
        "quality_status": "Green | Amber | Red",
        "rationale": "string",
    },
    "key_metrics": [
        {"metric": "string", "value": "string or number", "status": "Green | Amber | Red", "source": "string"}
    ],
    "timeline_summary": {
        "start_date": "YYYY-MM-DD or null",
        "target_go_live": "YYYY-MM-DD or null",
        "critical_path": ["string"],
        "upcoming_milestones": [{"milestone": "string", "date": "YYYY-MM-DD or null", "status": "string"}],
    },
    "budget_summary": {
        "currency": "string",
        "total_estimated_cost": 0,
        "confidence": "low | medium | high",
        "main_cost_drivers": ["string"],
    },
    "top_risks": [
        {"risk": "string", "severity": "Low | Medium | High", "mitigation": "string", "owner": "string"}
    ],
    "decisions_required": [
        {"decision": "string", "owner": "string", "needed_by": "YYYY-MM-DD or null", "impact": "string"}
    ],
    "recommendations": ["string"],
    "next_steps": [
        {"action": "string", "owner": "string", "due_date": "YYYY-MM-DD or null"}
    ],
    "traceability": [
        {"report_item": "string", "source_document": "BRD | User Stories | Planner | Budget", "evidence": "short quote or paraphrase"}
    ],
}


def executive_prompt(source_bundle_text: str) -> str:
    context = document_context(source_bundle_text, 28000)
    return (
        "You are the Executive Reporting Agent in a PMO workflow. "
        "Create a leadership-ready executive report from the BRD, user-story, planner, and budget outputs. "
        "Return exactly one valid JSON object and nothing else. Never use markdown or code fences. "
        "Ground every summary, risk, metric, and recommendation in the supplied documents. "
        "If a metric is missing, state that it is not available rather than inventing a value. "
        "The response must match this JSON shape and include every top-level key:\n"
        f"{json.dumps(EXECUTIVE_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Source documents:\n{context}"
    )


def executive_repair_prompt(source_bundle_text: str, invalid_response: Any, error: str) -> str:
    context = document_context(source_bundle_text, 28000)
    return (
        "Your previous Executive Reporting Agent response failed JSON/schema validation. "
        f"Validation error: {error}\n\n"
        "Return a corrected response as exactly one valid JSON object and nothing else. "
        "Include project_name, executive_summary, portfolio_health, key_metrics, timeline_summary, budget_summary, "
        "top_risks, decisions_required, recommendations, next_steps, and traceability. "
        "Do not use markdown or prose outside JSON.\n\n"
        f"Required JSON shape:\n{json.dumps(EXECUTIVE_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Previous invalid response:\n{to_json_text(invalid_response, 3500)}\n\n"
        f"Source documents:\n{context}"
    )

