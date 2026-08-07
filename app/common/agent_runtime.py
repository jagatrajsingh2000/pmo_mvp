import json
import logging
import re
from typing import Any, Callable, Dict, Iterable, Optional

from app.planner_agent.agent.azure_client import (
    AIJsonParseError,
    call_agno_azure_openai,
    has_azure_config,
)

logger = logging.getLogger(__name__)


COMMON_CONTEXT_KEYWORDS = (
    "project details",
    "executive summary",
    "business rationale",
    "scope",
    "stakeholders",
    "current state",
    "future state",
    "gap analysis",
    "functional requirements",
    "non-functional requirements",
    "integrations",
    "dependencies",
    "risks",
    "assumptions",
    "issues",
    "decisions",
    "solution approach",
    "acceptance criteria",
    "testing",
    "rollout",
    "change management",
    "governance",
    "sign-off",
    "gate plan",
    "budget",
    "cost",
    "benefits",
)


def require_azure_openai(agent_name: str) -> None:
    if not has_azure_config():
        raise RuntimeError(
            f"{agent_name} requires Azure OpenAI. Set AZURE_OPENAI_API_KEY, "
            "AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION, and AZURE_OPENAI_DEPLOYMENT."
        )


def document_context(document_text: str, max_chars: int = 20000) -> str:
    text = re.sub(r"\r\n?", "\n", document_text or "").strip()
    if len(text) <= max_chars:
        return text

    chunks = [text[:5000], text[-3000:]]
    lowered = text.lower()
    for keyword in COMMON_CONTEXT_KEYWORDS:
        start = lowered.find(keyword)
        if start < 0:
            continue
        left = max(0, start - 600)
        right = min(len(text), start + 2200)
        chunks.append(text[left:right])

    result = []
    seen = set()
    used = 0
    for chunk in chunks:
        normalized = re.sub(r"\s+", " ", chunk).strip()[:180]
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        if used + len(chunk) + 30 > max_chars:
            remaining = max_chars - used - 30
            if remaining <= 0:
                break
            chunk = chunk[:remaining]
        result.append(chunk)
        used += len(chunk) + 30
    return "\n\n--- source section ---\n\n".join(result)


def require_json_keys(payload: Dict[str, Any], required_keys: Iterable[str], label: str) -> None:
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must return one JSON object.")
    missing = [key for key in required_keys if key not in payload]
    if missing:
        raise RuntimeError(f"{label} response missing required keys: {', '.join(missing)}")


def generate_required_json(
    *,
    agent_name: str,
    prompt: str,
    required_keys: Iterable[str],
    repair_prompt: Optional[Callable[[Any, str], str]] = None,
    validator: Optional[Callable[[Dict[str, Any]], None]] = None,
    max_tokens: int = 12000,
    temperature: float = 0.1,
) -> Dict[str, Any]:
    """Call Azure OpenAI through Agno and validate required top-level keys.

    The optional repair pass is still Azure AI, not a deterministic fallback. It is
    used only to force valid JSON/schema conformance when the first response is
    malformed or incomplete.
    """
    require_azure_openai(agent_name)
    first_response: Any = None
    try:
        first_response = call_agno_azure_openai(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            request_label=agent_name,
        )
        require_json_keys(first_response, required_keys, agent_name)
        if validator:
            validator(first_response)
        return first_response
    except Exception as first_error:
        if repair_prompt is None:
            raise
        raw_response = first_error.raw_text if isinstance(first_error, AIJsonParseError) else first_response
        logger.warning("%s first response failed validation; asking Azure OpenAI to repair: %s", agent_name, first_error)
        repaired = call_agno_azure_openai(
            repair_prompt(raw_response or "", str(first_error)),
            max_tokens=max_tokens,
            temperature=temperature,
            request_label=f"{agent_name}_repair",
        )
        require_json_keys(repaired, required_keys, agent_name)
        if validator:
            validator(repaired)
        return repaired


def to_json_text(value: Any, max_chars: Optional[int] = None) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
    if max_chars and len(text) > max_chars:
        return text[:max_chars]
    return text
