import os
import openai


def call_azure_openai(prompt: str, max_tokens: int = 1500, temperature: float = 0.2):
    api_key = os.environ.get("AZURE_OPEN_API_KEY")
    api_base = os.environ.get("AZURE_OPENAI_API_ENDPOINT")
    api_version = os.environ.get("AZURE_OPEN_API_VERSION")
    deployment = os.environ.get("AZURE_OPEN_API_DEPLOYMENT")

    if not all([api_key, api_base, api_version, deployment]):
        raise RuntimeError("Missing Azure OpenAI environment variables")

    openai.api_type = "azure"
    openai.api_key = api_key
    openai.api_base = api_base
    openai.api_version = api_version

    messages = [
        {"role": "system", "content": "You are a helpful project timeline planner assistant."},
        {"role": "user", "content": prompt},
    ]

    resp = openai.ChatCompletion.create(
        model=deployment,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    # Extract text safely
    text = None
    try:
        text = resp.choices[0].message.content
    except Exception:
        text = str(resp)

    # Try to parse JSON; caller can handle if parsing fails
    try:
        import json

        return json.loads(text)
    except Exception:
        return {"text": text}
