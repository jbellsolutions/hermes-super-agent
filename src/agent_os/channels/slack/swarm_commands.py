"""Slack slash commands for the OpenSwarm fleet.

Two commands ship:

  /build-swarm <name> -- <description>
      Forks the OpenSwarm vendor into a new business-purpose swarm. The text
      after ``--`` is the natural-language description fed to the customizer
      (default: claude_code, override via ``customizer=manual`` etc.).

  /list-swarms
      Returns a one-line summary per registered fleet member.

The handlers below are dispatch-only — the gateway layer (Hermes' Slack
adapter) is responsible for verifying the request signature and delivering
the response. ``handle_command`` returns the Slack-shaped JSON payload so
the gateway just forwards it.
"""
from __future__ import annotations

import shlex
from typing import Any

from agent_os.runtimes.openswarm import invoke as openswarm_invoke


class CommandError(ValueError):
    """Surfaced to the user as an ephemeral message — not a server error."""


def handle_command(payload: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a Slack slash-command payload.

    Slack delivers ``command``, ``text``, ``user_id``, etc. We branch on
    ``command`` and parse ``text``. Returns a dict shaped for Slack's
    response_url (``response_type``, ``text``, optional ``blocks``).
    """
    cmd = (payload.get("command") or "").strip()
    text = (payload.get("text") or "").strip()
    if cmd in ("/build-swarm", "build-swarm"):
        return _handle_build(text)
    if cmd in ("/list-swarms", "list-swarms"):
        return _handle_list()
    return _ephemeral(f"Unknown command: {cmd!r}. Try /build-swarm or /list-swarms.")


# --------------------------------------------------------------------------
# /build-swarm
# --------------------------------------------------------------------------

def parse_build_args(text: str) -> dict[str, Any]:
    """Parse ``<name> [key=value ...] -- <description>``.

    Accepted keys: ``customizer``, ``validator``, ``cost_budget_daily_usd``.
    Values containing spaces must be quoted (shlex-style).

    Examples::

        seo-swarm -- SEO research and writing
        seo-swarm customizer=manual -- "SEO swarm for blogs"
        ops-swarm validator=noop cost_budget_daily_usd=5 -- "ops content"

    Raises CommandError on any malformed input.
    """
    if not text:
        raise CommandError("Usage: /build-swarm <name> [opts...] -- <description>")
    try:
        tokens = shlex.split(text)
    except ValueError as e:
        raise CommandError(f"could not parse args: {e}") from e
    if "--" not in tokens:
        raise CommandError(
            "Description required. Usage: /build-swarm <name> [opts...] -- <description>"
        )
    sep = tokens.index("--")
    head_tokens = tokens[:sep]
    description = " ".join(tokens[sep + 1 :]).strip()
    if not description:
        raise CommandError("Description must be non-empty after '--'.")
    if not head_tokens:
        raise CommandError("Swarm name required.")
    name, *opts = head_tokens
    options: dict[str, Any] = {}
    for tok in opts:
        if "=" not in tok:
            raise CommandError(f"option must be key=value, got {tok!r}")
        key, _, val = tok.partition("=")
        key = key.strip()
        val = val.strip()
        if key in ("customizer", "validator"):
            options[key] = val
        elif key == "cost_budget_daily_usd":
            try:
                options[key] = float(val)
            except ValueError as e:
                raise CommandError(f"cost_budget_daily_usd must be numeric: {val!r}") from e
        else:
            raise CommandError(f"unknown option: {key!r}")
    return {"name": name, "description": description, **options}


def _handle_build(text: str) -> dict[str, Any]:
    try:
        args = parse_build_args(text)
    except CommandError as e:
        return _ephemeral(f":warning: {e}")

    job: dict[str, Any] = {
        "op": "build",
        "name": args["name"],
        "description": args["description"],
    }
    for key in ("customizer", "validator", "cost_budget_daily_usd"):
        if key in args:
            job[key] = args[key]

    result = openswarm_invoke.invoke(job)
    if result.status != "ok":
        return _ephemeral(
            f":x: build failed for *{args['name']}*\n```{result.error}```"
        )
    out = result.output
    return _in_channel(
        f":white_check_mark: built *{out['name']}* on port {out['port']}\n"
        f"• customizer: `{out['customizer']}`  validator: `{out['validator']}`\n"
        f"• manifest: `{out['manifest_path']}`\n"
        f"• skill: `{out['skill_path']}`"
    )


# --------------------------------------------------------------------------
# /list-swarms
# --------------------------------------------------------------------------

def _handle_list() -> dict[str, Any]:
    result = openswarm_invoke.invoke({"op": "list"})
    if result.status != "ok":
        return _ephemeral(f":x: list failed: {result.error}")
    fleet = result.output or []
    if not fleet:
        return _ephemeral("Fleet is empty. Try `/build-swarm`.")
    lines = [
        f"• *{s['name']}* (port {s.get('port', '-')}) — `{s.get('live_status', '?')}` "
        f"— {s.get('business_purpose', '')}"
        for s in fleet
    ]
    return _in_channel("Fleet:\n" + "\n".join(lines))


# --------------------------------------------------------------------------
# response shapers
# --------------------------------------------------------------------------

def _ephemeral(text: str) -> dict[str, Any]:
    return {"response_type": "ephemeral", "text": text}


def _in_channel(text: str) -> dict[str, Any]:
    return {"response_type": "in_channel", "text": text}
