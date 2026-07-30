import json
import os
from typing import Any, Dict


def has_azure_config() -> bool:
    return all(
        [
            os.environ.get("AZURE_OPENAI_API_KEY"),
            os.environ.get("AZURE_OPENAI_ENDPOINT"),
            os.environ.get("AZURE_OPENAI_API_VERSION"),
            os.environ.get("AZURE_OPENAI_DEPLOYMENT"),
        ]
    )


def _parse_json_response(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        return {"text": text}


def call_azure_openai(prompt: str, max_tokens: int = 1500, temperature: float = 0.2) -> Dict[str, Any]:
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    api_base = os.environ.get("AZURE_OPENAI_ENDPOINT")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION")
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")

    if not all([api_key, api_base, api_version, deployment]):
        raise RuntimeError("Missing Azure OpenAI environment variables")

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
        )
        text = resp.choices[0].message.content or ""
    except Exception:
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

    return _parse_json_response(text)
