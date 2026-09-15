"""
Thin wrapper around a locally running Ollama instance.

Ollama exposes a REST API on http://localhost:11434 by default.
Install it from https://ollama.com and pull a model first, e.g.:

    ollama pull llama3.1

This keeps the whole AI pipeline free to run -- no OpenAI/Anthropic key
required. If Ollama isn't running, calls raise a clear error instead of
hanging silently, so the FastAPI endpoints can surface a useful message.
"""
import requests
import json
from typing import Optional

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:0.5b"  # change to whatever model you've pulled


class OllamaError(Exception):
    pass


def generate(prompt: str, model: str = DEFAULT_MODEL, system: Optional[str] = None,
             temperature: float = 0.3, num_predict: int = 500) -> str:
    """Single-shot generation call against Ollama's /api/generate endpoint."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "repeat_penalty": 1.3,
            "repeat_last_n": 256,
            "num_predict": num_predict,
        },
    }
    if system:
        payload["system"] = system

    try:
        resp = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=120)
        resp.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        raise OllamaError(
            "Could not reach Ollama at localhost:11434. Is it installed and running? "
            "Start it with `ollama serve` and make sure you've pulled a model "
            f"(`ollama pull {model}`)."
        ) from e
    except requests.exceptions.RequestException as e:
        raise OllamaError(f"Ollama request failed: {e}") from e

    data = resp.json()
    return data.get("response", "").strip()


def generate_json(prompt: str, model: str = DEFAULT_MODEL, system: Optional[str] = None) -> dict:
    """
    Ask the model to respond with strict JSON and parse it.
    Strips markdown code fences defensively since local models often add them.
    """
    raw = generate(prompt, model=model, system=system, temperature=0.2)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fall back: try to find the first {...} or [...] block
        start_candidates = [i for i in (cleaned.find("{"), cleaned.find("[")) if i != -1]
        if not start_candidates:
            raise OllamaError(f"Model did not return valid JSON: {raw[:300]}")
        start = min(start_candidates)
        end = max(cleaned.rfind("}"), cleaned.rfind("]")) + 1
        try:
            return json.loads(cleaned[start:end])
        except json.JSONDecodeError as e:
            raise OllamaError(f"Model did not return valid JSON: {raw[:300]}") from e


