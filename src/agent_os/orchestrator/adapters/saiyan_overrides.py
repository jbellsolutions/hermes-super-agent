"""Saiyan-mode runtime registry override.

The saiyan installer (install.py --mode=saiyan) copies the orchestrator
into a user's project but strips the fabric runtimes (coordinator,
vps_spawn, a2a_delegate, retell_channel, local_spawn). Rather than
rewriting the source of job_router.py with a fragile regex patch, the
installer also drops THIS file and adds two lines to the copied
adapters/__init__.py:

    from . import saiyan_overrides  # noqa: F401
    saiyan_overrides.apply()

This module imports job_router and mutates its registries in-place.
That way upstream refactors of _SYNC_RUNTIMES / _ASYNC_RUNTIMES don't
silently break every saiyan install — the override either applies
cleanly or raises a loud ImportError the user can act on.
"""
from __future__ import annotations

# Pure runtimes that ship in saiyan mode. Mirrors install.py's _PURE_RUNTIMES.
_SAIYAN_RUNTIMES = (
    "agent_zero",
    "aider",
    "browser_use",
    "claude_managed",
    "claude_subagents",
    "codex_cli",
    "computer_use",
    "e2b",
    "exa",
    "hermes_self",
    "livekit",
    "openclaw",
    "openswarm",
    "terminal",
)


def apply() -> None:
    """Trim the runtime registries to saiyan-only and rewrite dispatch error.

    Idempotent: re-running has no effect after the first call.
    """
    from agent_os.orchestrator.adapters import job_router as jr

    if getattr(jr, "_SAIYAN_APPLIED", False):
        return

    # 1. Strip fabric runtimes from the registries. We KEEP keys that match
    #    the saiyan set and drop everything else. This survives upstream
    #    additions of new runtimes — they're treated as fabric until the
    #    saiyan installer ships an update that whitelists them.
    saiyan_set = set(_SAIYAN_RUNTIMES)
    jr._SYNC_RUNTIMES = {k: v for k, v in jr._SYNC_RUNTIMES.items() if k in saiyan_set}
    jr._ASYNC_RUNTIMES = {k: v for k, v in jr._ASYNC_RUNTIMES.items() if k in saiyan_set}
    jr.KNOWN_RUNTIMES = set(jr._SYNC_RUNTIMES) | set(jr._ASYNC_RUNTIMES)

    # 2. Wrap dispatch() so that asking for a fabric runtime raises a
    #    friendly RuntimeError pointing at the upgrade path.
    original_dispatch = jr.dispatch

    async def saiyan_dispatch(job, plan=None):
        # Resolve runtime the same way the original does, but intercept
        # fabric requests BEFORE the original tries to import them.
        runtime = None
        if plan is not None:
            primary = getattr(plan, "primary_tool", None)
            if primary and primary in jr.KNOWN_RUNTIMES:
                runtime = primary
        if runtime is None:
            runtime = jr.route(job)
        if runtime not in jr.KNOWN_RUNTIMES:
            raise RuntimeError(
                f"runtime {runtime!r} needs the kaioken (local fabric) or "
                "super-saiyan-5 (cloud fabric) install. Saiyan mode ships "
                "only the 14 in-process runtimes. Upgrade with:\n"
                "  python3 install.py --mode=kaioken           # local Docker fabric\n"
                "  python3 install.py --mode=super-saiyan-5    # Railway + DO fabric\n"
                "See https://github.com/jbellsolutions/hermes-super-agent#picking-a-mode"
            )
        return await original_dispatch(job, plan=plan)

    jr.dispatch = saiyan_dispatch
    jr._SAIYAN_APPLIED = True
