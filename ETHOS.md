# Ethos — Stop Building, Start Layering

This repo exists because we shipped 14 framework wrappers in 6 weeks and none of them did the thing. The pathology was solo-rebuilding substrates that have ecosystem leaders.

## The rules

1. **Adopt > build.** Hermes (orchestrator), OpenClaw (autonomous-grind), browser-use (browser), Aider/Codex (coding), Anthropic Computer Use (desktop), AGI-1 (your quality edge) — all vendored as submodules, all auto-updated nightly. We do NOT rewrite these. We compose them.

2. **The moat is not the harness.** It's:
   - Your business graph (manifest + `/explain`)
   - Your prompts and skill library (DSPy-evolved, agi-1 promoted)
   - Your routing taste (which runtime per job)
   - Your single-state accessibility (Slack + Telegram + web chat + web voice → same Hermes)
   - The wired-together, daily-evolving stack — anyone can clone Hermes; very few will run it tied to a daily-updating quality flywheel.

3. **The 5-question filter on every shiny new launch:**
   1. Plugs into tools we already use, or demands migration? → migration = hard pass.
   2. Lets other agents build on it (MCP/SDK/API)? → closed = feature, not infra.
   3. Owns or accesses data we care about? → no = not infra.
   4. Ecosystem momentum (stars, weekly releases, marketplace, partners)? → no = science project.
   5. Can our manifest layer stack on top? → no = silo, skip.

   **4-of-5 yes → afternoon. 3 or fewer → memory it for later.**

4. **Frustration is not a license to fork.** When Hermes/OpenClaw/Aider misbehaves: open an issue upstream, write an adapter in `packages/runtimes/<name>/`, or extend the manifest. Never start a 15th framework repo.

5. **No editing `vendor/`.** Submodules are the OSS we adopted. If you need a change: PR upstream or wrap in `packages/`. Editing vendored code breaks the auto-updater.

6. **Smoke tests are non-negotiable for the upgrader.** A bad upstream commit silently promoted is the only failure mode that takes the whole system down.

7. **Default to Hermes.** Most jobs don't need a specialist runtime. The router is a small switch statement, not a strategy pattern.

8. **Markdown vault is the source of truth.** Human-readable, grep-able, git-versionable. Supabase is a mirror, not the primary.

9. **Single-state guarantee or the product doesn't exist.** Slack, Telegram, web chat, web voice — all hit the same Hermes with the same memory. If a channel breaks single-state, the channel is wrong, not Hermes.

10. **Self-* claims must have a state machine.** Self-healing → genome incident loop. Self-learning → DSPy autoresearch with binary assertions. Self-growing → upgrader streams. Self-skills → Hermes save + agi-1 promote. No vibes.

## Health check (monthly)

Total custom code (lines outside `vendor/`) holds flat or decreases month-over-month while shipped vertical apps in `examples/` increase. If custom LOC is climbing, we've drifted back into the pathology.
