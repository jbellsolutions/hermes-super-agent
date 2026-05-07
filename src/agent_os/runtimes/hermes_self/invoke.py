"""hermes_self runtime — the default. Admiral handles the prompt itself.

When a user types "summarize this" or "what's on the calendar" in Telegram,
no specialist runtime matches and `route()` returns 'hermes_self'. This
runtime makes one LLM call (model from HERMES_DEFAULT_MODEL or
COORDINATOR_DEFAULT_MODEL) and returns the response.

Without this runtime the dispatch table would fail on every plain
conversation message — the import error would crash the bot handler.

Auth: ANTHROPIC_API_KEY for claude-* models; OPENAI_API_KEY for gpt-*;
delegated to OpenRouter for everything else.

Returns a RuntimeResult so it conforms to the same shape every other
sync runtime uses.
"""
from __future__ import annotations

import logging
import os
import time

from agent_os.runtimes._base import RuntimeResult, new_job_id, write_run_artifact

logger = logging.getLogger(__name__)


def _default_model() -> str:
    return (
        os.getenv("HERMES_DEFAULT_MODEL")
        or os.getenv("COORDINATOR_DEFAULT_MODEL")
        or "claude-sonnet-4-5"
    )


def invoke(job) -> RuntimeResult:
    """Run a single LLM call for the job's prompt."""
    t0 = time.time()
    job_id = new_job_id()

    prompt = getattr(job, "prompt", None) or (job.get("prompt") if isinstance(job, dict) else "")
    model = (getattr(job, "metadata", {}) or {}).get("model") or _default_model()

    if not prompt:
        return _result(job_id, "error", {"error": "empty prompt"}, t0)

    try:
        text = _call_llm(model, prompt)
    except Exception as exc:
        logger.warning("hermes_self LLM call failed: %s", exc)
        return _result(job_id, "error", {"error": str(exc), "model": model}, t0)

    return _result(job_id, "completed", {"text": text, "model": model}, t0)


def _call_llm(model: str, prompt: str) -> str:
    """Single chat completion. Routes by model id prefix."""
    if model.startswith("claude-"):
        return _call_anthropic(model, prompt)
    return _call_openai_compat(model, prompt)


def _call_anthropic(model: str, prompt: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set — cannot call claude")

    from anthropic import Anthropic  # imported lazily so missing dep doesn't block boot
    client = Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in msg.content if hasattr(b, "text"))


def _call_openai_compat(model: str, prompt: str) -> str:
    base_url, api_key = _resolve_openai_compat(model)
    if not api_key:
        raise RuntimeError(f"No API key configured for model {model!r}")

    from openai import OpenAI
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    client = OpenAI(**kwargs)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
    )
    return resp.choices[0].message.content or ""


def _resolve_openai_compat(model: str) -> tuple[str | None, str]:
    """Same routing as the coordinator service — keep them in sync."""
    if model.startswith(("gpt-", "o1", "o3", "chatgpt-")):
        return None, os.getenv("OPENAI_API_KEY", "")
    if model.startswith("deepseek"):
        return "https://api.deepseek.com/v1", os.getenv("DEEPSEEK_API_KEY", "")
    if model.startswith(("kimi", "moonshot")):
        return "https://api.moonshot.ai/v1", os.getenv("MOONSHOT_API_KEY", "")
    if model.startswith(("gemini", "google/")):
        return "https://generativelanguage.googleapis.com/v1beta/openai", os.getenv("GOOGLE_API_KEY", "")
    return "https://openrouter.ai/api/v1", os.getenv("OPENROUTER_API_KEY", "")


def _result(job_id: str, status: str, output: dict, t0: float) -> RuntimeResult:
    result = RuntimeResult(
        runtime="hermes_self",
        job_id=job_id,
        status=status,
        output=output,
        latency_ms=int((time.time() - t0) * 1000),
    )
    write_run_artifact(result)
    return result
