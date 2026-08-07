import json
from typing import Any

from app.common.agent_runtime import document_context, to_json_text

BUDGET_REQUIRED_KEYS = (
    "project_name",
    "summary",
    "currency",
    "cost_summary",
    "workstream_estimates",
    "resource_costs",
    "timeline_budget",
    "budget_risks",
    "recommendations",
    "traceability",
)

BUDGET_JSON_CONTRACT = {
    "project_name": "string",
    "summary": "string",
    "currency": "USD | INR | AED | THB | not specified",
    "cost_summary": {
        "total_estimated_cost": 0,
        "capex": 0,
        "opex": 0,
        "contingency": 0,
        "confidence": "low | medium | high",
        "basis": "string",
    },
    "workstream_estimates": [
        {
            "workstream": "Analysis | Architecture | Development | Integration | Testing | Deployment | Hypercare",
            "effort_level": "Low | Medium | High",
            "person_days": 0,
            "cost": 0,
            "assumptions": "string",
        }
    ],
    "resource_costs": [
        {
            "role": "string",
            "count": "number or string",
            "duration_weeks": 0,
            "rate_assumption": "string",
            "estimated_cost": 0,
            "scope_notes": "string",
        }
    ],
    "timeline_budget": [
        {
            "phase": "string",
            "start_date": "YYYY-MM-DD or null",
            "end_date": "YYYY-MM-DD or null",
            "estimated_cost": 0,
            "cost_driver": "string",
        }
    ],
    "budget_risks": [
        {"risk": "string", "impact": "Low | Medium | High", "mitigation": "string", "owner": "string"}
    ],
    "recommendations": ["string"],
    "traceability": [
        {"budget_item": "string", "source_reference": "planner/WBS/resource evidence", "confidence": "low | medium | high"}
    ],
}


def budget_prompt(document_text: str) -> str:
    context = document_context(document_text, 22000)
    return (
        "You are the Budget Agent in a PMO workflow. "
        "Create a project budgeting and financial planning output from the planner document. "
        "Return exactly one valid JSON object and nothing else. Never use markdown or code fences. "
        "Ground cost and effort estimates in the source WBS, schedule, resource allocation, effort estimation, and risks. "
        "If actual rates or currency are missing, set numeric costs to 0 where needed and explain the rate/currency assumption in basis fields. "
        "Do not invent vendor prices. Make uncertainty explicit. "
        "The response must match this JSON shape and include every top-level key:\n"
        f"{json.dumps(BUDGET_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Planner document content:\n{context}"
    )


def budget_repair_prompt(document_text: str, invalid_response: Any, error: str) -> str:
    context = document_context(document_text, 22000)
    return (
        "Your previous Budget Agent response failed JSON/schema validation. "
        f"Validation error: {error}\n\n"
        "Return a corrected response as exactly one valid JSON object and nothing else. "
        "Include project_name, summary, currency, cost_summary, workstream_estimates, resource_costs, timeline_budget, budget_risks, recommendations, and traceability. "
        "Do not use markdown or prose outside JSON.\n\n"
        f"Required JSON shape:\n{json.dumps(BUDGET_JSON_CONTRACT, ensure_ascii=False, indent=2)}\n\n"
        f"Previous invalid response:\n{to_json_text(invalid_response, 3500)}\n\n"
        f"Planner document content:\n{context}"
    )

