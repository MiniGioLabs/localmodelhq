"""Ollama REST API service."""

import httpx
from ..config import settings


async def get_installed_models() -> list[dict]:
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{settings.OLLAMA_URL}/api/tags", timeout=5)
            return r.json().get("models", [])
    except Exception:
        return []


async def get_running_models() -> list[dict]:
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get(f"{settings.OLLAMA_URL}/api/ps", timeout=5)
            return r.json().get("models", [])
    except Exception:
        return []


async def pull_model(model_tag: str):
    """Stream model pull progress. Yields status dicts."""
    async with httpx.AsyncClient(timeout=None) as c:
        async with c.stream(
            "POST", f"{settings.OLLAMA_URL}/api/pull",
            json={"name": model_tag}
        ) as r:
            async for line in r.aiter_lines():
                if line:
                    import json
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        pass


async def delete_model(model_tag: str) -> bool:
    try:
        async with httpx.AsyncClient() as c:
            r = await c.delete(
                f"{settings.OLLAMA_URL}/api/delete",
                json={"name": model_tag},
                timeout=30
            )
            return r.status_code == 200
    except Exception:
        return False


async def generate(model_tag: str, prompt: str) -> dict:
    """Run a single generation and return timing metrics."""
    import time
    async with httpx.AsyncClient(timeout=120) as c:
        start = time.perf_counter()
        first_token = None
        total_tokens = 0
        response_text = ""

        async with c.stream(
            "POST", f"{settings.OLLAMA_URL}/api/generate",
            json={"model": model_tag, "prompt": prompt, "stream": True}
        ) as r:
            async for line in r.aiter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if first_token is None:
                            first_token = time.perf_counter()
                        if "response" in chunk:
                            response_text += chunk["response"]
                        if "eval_count" in chunk:
                            total_tokens = chunk["eval_count"]
                    except json.JSONDecodeError:
                        pass

        duration = (time.perf_counter() - start) * 1000
        first_token_ms = (first_token - start) * 1000 if first_token else 0
        tps = total_tokens / (duration / 1000) if duration > 0 and total_tokens > 0 else 0

        return {
            "response": response_text.strip(),
            "duration_ms": round(duration, 1),
            "tokens_per_sec": round(tps, 1),
            "total_tokens": total_tokens,
            "first_token_ms": round(first_token_ms, 1),
        }
