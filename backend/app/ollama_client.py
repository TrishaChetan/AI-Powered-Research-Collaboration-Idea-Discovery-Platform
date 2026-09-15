"""
Fast wrapper around a locally running Ollama instance.
"""

import requests
import json
import re
from typing import Optional

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:0.5b"

# Reuse one HTTP session instead of creating a new connection for every request.
_session = requests.Session()


class OllamaError(Exception):
    pass


def generate(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system: Optional[str] = None,
    temperature: float = 0.3,
    num_predict: int = 300,
) -> str:
    """Generate a response from Ollama."""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "10m",
        "options": {
            "temperature": temperature,
            "repeat_penalty": 1.15,
            "repeat_last_n": 64,
            "num_predict": num_predict,
        },
    }

    if system:
        payload["system"] = system

    try:
        resp = _session.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()

    except requests.exceptions.ConnectionError as e:
        raise OllamaError(
            "Could not reach Ollama at localhost:11434. "
            "Make sure Ollama is running."
        ) from e

    except requests.exceptions.RequestException as e:
        raise OllamaError(f"Ollama request failed: {e}") from e

    data = resp.json()
    return data.get("response", "").strip()


def generate_json(
    prompt: str,
    model: str = DEFAULT_MODEL,
    system: Optional[str] = None,
    num_predict: int = 300,
) -> dict:
    """Generate and parse a JSON response from Ollama."""

    raw = generate(
        prompt,
        model=model,
        system=system,
        temperature=0.2,
        num_predict=num_predict,
    )

    cleaned = raw.strip()

    # Remove markdown code fences if the model adds them.
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]

    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError:
        # Try to recover the first JSON object/array.
        start_candidates = [
            i for i in (cleaned.find("{"), cleaned.find("[")) if i != -1
        ]

        if not start_candidates:
            raise OllamaError(
                f"Model did not return valid JSON: {raw[:300]}"
            )

        start = min(start_candidates)
        end = max(
            cleaned.rfind("}"),
            cleaned.rfind("]")
        ) + 1

        try:
            return json.loads(cleaned[start:end])

        except json.JSONDecodeError as e:
            raise OllamaError(
                f"Model did not return valid JSON: {raw[:300]}"
            ) from e



