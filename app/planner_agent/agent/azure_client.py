import json
import logging
import os
import re
from inspect import Parameter, signature
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class AIJsonParseError(RuntimeError):
    def __init__(self, message: str, raw_text: str, finish_reason: Optional[str] = None):
        super().__init__(message)
        self.raw_text = raw_text
        self.finish_reason = finish_reason


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
        "provider": "agno_azure_openai" if has_azure_config() else "not_configured",
    }


def _parse_json_response(text: str, finish_reason: Optional[str] = None) -> Dict[str, Any]:
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
        logger.warning(
            "Azure OpenAI response was not valid JSON. response_length=%s finish_reason=%s preview=%r tail=%r",
            len(text),
            finish_reason,
            text[:500],
            text[-500:],
        )
        if finish_reason == "length":
            raise AIJsonParseError(
                "Azure OpenAI response was truncated before valid JSON completed. Increase AZURE_OPENAI_MAX_TOKENS or reduce input size.",
                text,
                finish_reason,
            )
        raise AIJsonParseError("Azure OpenAI response was not valid JSON.", text, finish_reason)


def call_agno_azure_openai(
    prompt: str,
    max_tokens: Optional[int] = None,
    temperature: float = 0.1,
    request_label: Optional[str] = None,
) -> Dict[str, Any]:
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    api_base = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")

    if not all([api_key, api_base, api_version, deployment]):
        raise RuntimeError("Missing Azure OpenAI environment variables")
    token_budget = max_tokens or int(os.environ.get("AZURE_OPENAI_MAX_TOKENS", "12000"))

    logger.info(
        "Azure OpenAI request starting label=%s deployment=%s api_version=%s prompt_chars=%s max_tokens=%s",
        request_label or "unknown",
        deployment,
        api_version,
        len(prompt),
        token_budget,
    )
    os.environ["AZURE_OPENAI_API_KEY"] = api_key
    os.environ["AZURE_OPENAI_ENDPOINT"] = api_base
    os.environ["AZURE_OPENAI_API_VERSION"] = api_version
    os.environ["AZURE_DEPLOYMENT"] = deployment

    try:
        from agno.agent import Agent
        from agno.models.azure import AzureOpenAI
    except Exception as exc:
        raise RuntimeError("Agno is not installed. Install backend requirements with `python -m pip install -r requirements.txt`.") from exc

    base_model_kwargs = {
        "id": deployment,
        "api_key": api_key,
        "azure_endpoint": api_base,
        "api_version": api_version,
        "azure_deployment": deployment,
        "temperature": temperature,
        "max_tokens": token_budget,
    }
    try:
        params = signature(AzureOpenAI).parameters
        accepts_kwargs = any(param.kind == Parameter.VAR_KEYWORD for param in params.values())
        model_kwargs = {
            key: value
            for key, value in base_model_kwargs.items()
            if accepts_kwargs or key in params
        }
    except Exception:
        model_kwargs = {"id": deployment}
    model = AzureOpenAI(**model_kwargs)
    agent = Agent(
        model=model,
        markdown=False,
        instructions=[
            "You are a PMO planning assistant.",
            "Return only one valid JSON object.",
            "Do not include markdown, code fences, comments, explanations, or prose outside JSON.",
        ],
        use_json_mode=True,
    )
    run = agent.run(prompt)
    text = getattr(run, "content", run) or ""
    if not isinstance(text, str):
        text = json.dumps(text, ensure_ascii=False)
    finish_reason = getattr(run, "finish_reason", None)

    parsed = _parse_json_response(text, finish_reason)
    logger.info(
        "Agno Azure OpenAI request completed label=%s parsed_keys=%s finish_reason=%s usage=%s",
        request_label or "unknown",
        sorted(parsed.keys()),
        finish_reason,
        getattr(run, "metrics", None),
    )
    return parsed
