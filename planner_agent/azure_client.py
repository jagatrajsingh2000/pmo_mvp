import json
import logging
import os
import re
from typing import Any, Dict

logger = logging.getLogger(__name__)


def has_azure_config() -> bool:
    return all(
        [
            os.environ.get("AZURE_OPENAI_API_KEY"),
            os.environ.get("AZURE_OPENAI_ENDPOINT"),
            os.environ.get("AZURE_OPENAI_API_VERSION"),
            os.environ.get("AZURE_OPENAI_DEPLOYMENT"),
        ]
    )


def feature_fallback_enabled() -> bool:
    value = os.environ.get("FEATURE_FALLBACK", "False")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def planner_status() -> Dict[str, Any]:
    return {
        "azure_openai_configured": has_azure_config(),
        "feature_fallback_enabled": feature_fallback_enabled(),
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
        return {"text": text}


def call_azure_openai(prompt: str, max_tokens: int = 1500, temperature: float = 0.2) -> Dict[str, Any]:
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    api_base = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")

    if not all([api_key, api_base, api_version, deployment]):
        raise RuntimeError("Missing Azure OpenAI environment variables")

    logger.info(
        "Azure OpenAI request starting deployment=%s api_version=%s prompt_chars=%s",
        deployment,
        api_version,
        len(prompt),
    )
    messages = [
        {"role": "system", "content": "You are a helpful project timeline planner assistant."},
        {"role": "user", "content": prompt},
    ]

    try:
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
    except Exception as exc:
        logger.warning("AzureOpenAI client request failed, trying legacy SDK path: %s", exc)
        import openai

        openai.api_type = "azure"
        openai.api_key = api_key
        openai.api_base = api_base
        openai.api_version = api_version
        resp = openai.ChatCompletion.create(
            model=deployment,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        text = resp.choices[0].message.content

    parsed = _parse_json_response(text)
    logger.info("Azure OpenAI request completed parsed_keys=%s", sorted(parsed.keys()))
    return parsed
