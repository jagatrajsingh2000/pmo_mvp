import json
import logging
import os
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AIJsonParseError(RuntimeError):
    def __init__(self, message: str, raw_text: str):
        super().__init__(message)
        self.raw_text = raw_text


def has_azure_config() -> bool:
    return all(
        [
            os.environ.get("AZURE_OPENAI_API_KEY"),
            os.environ.get("AZURE_OPENAI_ENDPOINT"),
            os.environ.get("AZURE_OPENAI_API_VERSION"),
            os.environ.get("AZURE_OPENAI_DEPLOYMENT"),
        ]
    )


def planner_status() -> Dict[str, Any]:
    return {
        "azure_openai_configured": has_azure_config(),
        "provider": "azure_openai" if has_azure_config() else "not_configured",
    }


def _parse_json_response(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        logger.warning("Azure OpenAI response was not valid JSON. response_length=%s", len(text))
        raise AIJsonParseError("Azure OpenAI response was not valid JSON.", text)


def call_azure_openai(
    prompt: str,
    max_tokens: int = 4096,
    temperature: float = 0.1,
    request_label: Optional[str] = None,
) -> Dict[str, Any]:
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    api_base = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")

    if not all([api_key, api_base, api_version, deployment]):
        raise RuntimeError("Missing Azure OpenAI environment variables")

    logger.info(
        "Azure OpenAI request starting label=%s deployment=%s api_version=%s prompt_chars=%s max_tokens=%s",
        request_label or "unknown",
        deployment,
        api_version,
        len(prompt),
        max_tokens,
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are a PMO planning assistant. Return only one valid JSON object. "
                "Do not include markdown, code fences, comments, explanations, or prose outside JSON."
            ),
        },
        {"role": "user", "content": prompt},
    ]

    from openai import AzureOpenAI

    client = AzureOpenAI(
        api_key=api_key,
        azure_endpoint=api_base,
        api_version=api_version,
    )
    resp = client.chat.completions.create(
        model=deployment,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    text = resp.choices[0].message.content or ""

    parsed = _parse_json_response(text)
    usage = getattr(resp, "usage", None)
    logger.info(
        "Azure OpenAI request completed label=%s parsed_keys=%s usage=%s",
        request_label or "unknown",
        sorted(parsed.keys()),
        usage,
    )
    return parsed
