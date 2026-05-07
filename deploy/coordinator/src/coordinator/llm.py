"""Multi-backend LLM router.

Resolves a model id to the right backend (Anthropic / OpenAI / DeepSeek /
Moonshot / OpenRouter / Google) and makes a single chat completion call.

Add a new model family by adding one branch to ``_resolve_backend``.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LLMResult:
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


async def call_llm(model: str, prompt: str, system: str = "", max_tokens: int = 4096) -> LLMResult:
    """Single chat completion. Routes by model id prefix.

    Default fallback must match the `default` task_class in
    src/agent_os/orchestrator/config/models.yaml so the coordinator
    and hermes_self runtime stay in sync.
    """
    if not model:
        model = os.getenv("COORDINATOR_DEFAULT_MODEL", "claude-sonnet-4.7")

    if model.startswith("claude-"):
        return await _call_anthropic(model, prompt, system, max_tokens)
    return await _call_openai_compat(model, prompt, system, max_tokens)


async def _call_anthropic(model: str, prompt: str, system: str, max_tokens: int) -> LLMResult:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    from anthropic import AsyncAnthropic
    client = AsyncAnthropic(api_key=api_key)
    msg = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system or "You are a helpful agent in a fan-out swarm.",
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in msg.content if hasattr(b, "text"))
    return LLMResult(
        text=text,
        model=model,
        input_tokens=msg.usage.input_tokens,
        output_tokens=msg.usage.output_tokens,
    )


async def _call_openai_compat(model: str, prompt: str, system: str, max_tokens: int) -> LLMResult:
    base_url, api_key = _resolve_openai_compat(model)
    if not api_key:
        raise RuntimeError(f"No API key configured for model '{model}'")

    from openai import AsyncOpenAI
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    client = AsyncOpenAI(**kwargs)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    resp = await client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
    )
    return LLMResult(
        text=resp.choices[0].message.content or "",
        model=model,
        input_tokens=getattr(resp.usage, "prompt_tokens", 0) or 0,
        output_tokens=getattr(resp.usage, "completion_tokens", 0) or 0,
    )


def _resolve_openai_compat(model: str) -> tuple[str | None, str]:
    """Map a model id to (base_url, api_key) for OpenAI-compatible endpoints."""
    if model.startswith(("gpt-", "o1", "o3", "chatgpt-")):
        return None, os.getenv("OPENAI_API_KEY", "")
    if model.startswith("deepseek"):
        return "https://api.deepseek.com/v1", os.getenv("DEEPSEEK_API_KEY", "")
    if model.startswith(("kimi", "moonshot")):
        return "https://api.moonshot.ai/v1", os.getenv("MOONSHOT_API_KEY", "")
    if model.startswith(("gemini", "google/")):
        return "https://generativelanguage.googleapis.com/v1beta/openai", os.getenv("GOOGLE_API_KEY", "")
    # Catch-all: OpenRouter accepts any model id in the form "vendor/model".
    return "https://openrouter.ai/api/v1", os.getenv("OPENROUTER_API_KEY", "")
