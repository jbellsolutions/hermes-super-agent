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
from pathlib import Path

from agent_os.runtimes._base import RuntimeResult, new_job_id, write_run_artifact

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Identity — loaded once per identity name, keyed by AGENT_IDENTITY env var.
#
# Each deployed agent sets AGENT_IDENTITY=<name> (e.g. coo, gtm, head_of_ops,
# supersan). The name maps directly to a YAML file in
# orchestrator/config/identities/<name>.yaml.
# Defaults to "supersan" if unset.
# ---------------------------------------------------------------------------

_IDENTITY_ROOT = Path(__file__).parents[3] / "orchestrator/config/identities"
_PROMPT_CACHE: dict[str, str] = {}


def _get_system_prompt(identity: str | None = None) -> str:
    name = identity or os.getenv("AGENT_IDENTITY", "supersan")
    if name in _PROMPT_CACHE:
        return _PROMPT_CACHE[name]
    try:
        import yaml  # noqa: PLC0415
        p = _IDENTITY_ROOT / f"{name}.yaml"
        data = yaml.safe_load(p.read_text())
        _PROMPT_CACHE[name] = (data.get("system_prompt") or "").strip()
    except Exception as exc:
        logger.warning("Could not load system prompt for identity %r: %s", name, exc)
        _PROMPT_CACHE[name] = ""
    return _PROMPT_CACHE[name]


# ---------------------------------------------------------------------------
# Model selection
# ---------------------------------------------------------------------------

def _default_model() -> str:
    """Final fallback — must match `default` task_class in config/models.yaml."""
    return (
        os.getenv("HERMES_DEFAULT_MODEL")
        or os.getenv("COORDINATOR_DEFAULT_MODEL")
        or "claude-sonnet-4.7"
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def invoke(job) -> RuntimeResult:
    """Run a single LLM call for the job's prompt.

    Model selection precedence (highest first):
      1. job.metadata['model']                — caller pinned a model
      2. job.metadata['model_recommendation'] — planner's pick
      3. HERMES_DEFAULT_MODEL env             — deployment default
      4. COORDINATOR_DEFAULT_MODEL env        — fleet-wide fallback
      5. claude-sonnet-4.7                    — final fallback (matches models.yaml)
    """
    t0 = time.time()
    job_id = new_job_id()

    prompt = getattr(job, "prompt", None) or (job.get("prompt") if isinstance(job, dict) else "")
    meta = getattr(job, "metadata", None) or {}
    if not isinstance(meta, dict):
        meta = {}
    model = meta.get("model") or meta.get("model_recommendation") or _default_model()
    user_id = meta.get("user_id", "default")
    identity = meta.get("identity")  # optional per-job override; falls back to AGENT_IDENTITY env

    if not prompt:
        return _result(job_id, "error", {"error": "empty prompt"}, t0)

    # Load identity and conversation history before the LLM call
    from agent_os.orchestrator.adapters import vault_memory as _vault  # noqa: PLC0415
    system_prompt = _get_system_prompt(identity)
    history = _vault.parse_history(user_id, limit=10)

    try:
        text = _call_llm(model, prompt, system_prompt=system_prompt, history=history)
    except Exception as exc:
        logger.warning("hermes_self LLM call failed: %s", exc)
        return _result(job_id, "error", {"error": str(exc), "model": model}, t0)

    # Persist both turns so the next call can load them as context
    _vault.append_message(user_id, "user", prompt)
    _vault.append_message(user_id, "assistant", text)

    return _result(job_id, "completed", {"text": text, "model": model}, t0)


# ---------------------------------------------------------------------------
# LLM dispatch
# ---------------------------------------------------------------------------

def _call_llm(
    model: str,
    prompt: str,
    *,
    system_prompt: str = "",
    history: list | None = None,
) -> str:
    """Single chat completion. Routes by model id prefix."""
    if model.startswith("claude-"):
        return _call_anthropic(model, prompt, system_prompt=system_prompt, history=history)
    return _call_openai_compat(model, prompt, system_prompt=system_prompt, history=history)


def _call_anthropic(
    model: str,
    prompt: str,
    *,
    system_prompt: str = "",
    history: list | None = None,
) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set — cannot call claude")

    from anthropic import Anthropic  # imported lazily so missing dep doesn't block boot
    client = Anthropic(api_key=api_key)

    messages = list(history or [])
    messages.append({"role": "user", "content": prompt})

    kwargs: dict = {"model": model, "max_tokens": 2048, "messages": messages}
    if system_prompt:
        kwargs["system"] = system_prompt

    msg = client.messages.create(**kwargs)
    return "".join(b.text for b in msg.content if hasattr(b, "text"))


def _call_openai_compat(
    model: str,
    prompt: str,
    *,
    system_prompt: str = "",
    history: list | None = None,
) -> str:
    base_url, api_key = _resolve_openai_compat(model)
    if not api_key:
        raise RuntimeError(f"No API key configured for model {model!r}")

    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history or [])
    messages.append({"role": "user", "content": prompt})

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
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
        return (
            "https://generativelanguage.googleapis.com/v1beta/openai",
            os.getenv("GOOGLE_API_KEY", ""),
        )
    return "https://openrouter.ai/api/v1", os.getenv("OPENROUTER_API_KEY", "")


# ---------------------------------------------------------------------------
# Result helper
# ---------------------------------------------------------------------------

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
