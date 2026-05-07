"""Verify _resolve_openai_compat picks the right backend per model id.

This is a pure-function test — no network, no API keys needed.
"""
from __future__ import annotations

import pytest


@pytest.mark.parametrize("model,want_base,want_env", [
    ("gpt-4o",                          None,                                                "OPENAI_API_KEY"),
    ("gpt-5",                           None,                                                "OPENAI_API_KEY"),
    ("o1-preview",                      None,                                                "OPENAI_API_KEY"),
    ("o3-mini",                         None,                                                "OPENAI_API_KEY"),
    ("chatgpt-4o-latest",               None,                                                "OPENAI_API_KEY"),
    ("deepseek-v4-pro",                 "https://api.deepseek.com/v1",                       "DEEPSEEK_API_KEY"),
    ("deepseek-chat",                   "https://api.deepseek.com/v1",                       "DEEPSEEK_API_KEY"),
    ("kimi-k2",                         "https://api.moonshot.ai/v1",                        "MOONSHOT_API_KEY"),
    ("moonshot-v1-128k",                "https://api.moonshot.ai/v1",                        "MOONSHOT_API_KEY"),
    ("gemini-2.5-pro",                  "https://generativelanguage.googleapis.com/v1beta/openai", "GOOGLE_API_KEY"),
    ("google/gemini-1.5",               "https://generativelanguage.googleapis.com/v1beta/openai", "GOOGLE_API_KEY"),
    # Catch-all — anything else routes through OpenRouter
    ("anthropic/claude-foo",            "https://openrouter.ai/api/v1",                      "OPENROUTER_API_KEY"),
    ("mistral/mistral-large",           "https://openrouter.ai/api/v1",                      "OPENROUTER_API_KEY"),
    ("meta-llama/llama-3-70b",          "https://openrouter.ai/api/v1",                      "OPENROUTER_API_KEY"),
])
def test_router_resolves_backend(monkeypatch, model, want_base, want_env):
    monkeypatch.setenv(want_env, "test-key-value")
    from coordinator.llm import _resolve_openai_compat
    base, key = _resolve_openai_compat(model)
    assert base == want_base, f"{model} → wrong base_url"
    assert key == "test-key-value", f"{model} → wrong env var (looked for {want_env})"


def test_claude_does_not_go_through_openai_compat():
    """Claude models route to Anthropic SDK, not the OpenAI-compat fallback."""
    # Direct check: call_llm dispatches based on model.startswith('claude-')
    import inspect
    from coordinator.llm import call_llm
    src = inspect.getsource(call_llm)
    assert 'startswith("claude-")' in src
    assert "_call_anthropic" in src
