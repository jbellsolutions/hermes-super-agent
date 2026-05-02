# The Story of agent-os

> *How we got from 14 broken frameworks to one agent that actually works.*

## Act I — The Pile

Six weeks. Seventy-four repositories.

That's how many AI-agent projects landed in `jbellsolutions` GitHub between February and April 2026. Forge. Agent Core. COO Agent. Agent Company. Ultimate Agent Framework. Division Builder. AGI-1. Operations Core. Ops-OS. Agent Stack. Fleet Builder. Coo-Platform. Coo-Dashboard. GStack. And another fifty-some vertical apps stacked on top.

Each one looked good in the README. Each one had the *features*. None of them did the thing.

Forge designed swarms — but it wasn't always-on. Agent Core was always-on — but it was one brain, not a fleet. AGI-1 was a quality flywheel — but when you ran it on a project, the project didn't get better. Coo-agent was the closest thing to an always-on COO — but it was tangled with Paperclip and Computer Use and you couldn't lift it out.

Every repo had a slice of the answer. None had the whole.

The frustration cycle went like this: ship a wrapper. Hit a wall. Open a new repo to "do it right this time." Rinse. Repeat. Fourteen times.

Justin's exact words on the founding call:

> "When we made our own SDK, it has all the features that are supposed to work, but it doesn't actually work and it's not actually helpful or really doing what we want it to. Same with AGI-1 — when I apply it to a repository, it doesn't seem to really make it better."

That's not a tooling problem. That's a *pattern*.

## Act II — The Realization

The reframe came from two videos and one filter.

**Nate Jones** said the agent market wasn't moving toward one product. It was moving toward layers. Stop asking "which agent should I switch to?" Start asking "which layer is each piece of work the right shape for?" Run every shiny launch through five questions: Does it plug in, or demand migration? Open or closed? Owns the data you care about? Ecosystem momentum? Stackable? Four-of-five → take it seriously. Three or fewer → memory it for later.

**Eric Hsu** showed what the layer composition looked like in practice. Hermes (the brain — persistent, self-improving, lives on your server). OpenClaw (the arms — autonomous, battle-tested, 300,000 GitHub stars). Two systems, holding each other accountable. When OpenClaw's gateway crashes, Hermes restarts it. When Hermes forgets a cron, OpenClaw catches it. The whole greater than the sum.

The filter was simple: **stop building, start composing.**

That cut the answer in half. The other half was uniquely Justin's: **fourteen frameworks were the disease; consolidation was a temptation, not a cure.** Merging fourteen wrappers into one wrapper is still building a wrapper. The honest move was to delete the wrappers entirely — adopt the OSS leaders, vendor them, auto-update them, and write only the thin glue that's genuinely yours.

What's genuinely yours? Three things, and only three:

1. **Your business graph** — the agents, tools, customers, decisions, outputs, indexed so you can actually query "how does cold-email-agent connect to speakeragent-api?" and get an answer.
2. **Your prompts and skill library** — refined on your real data, evolved by autoresearch loops against binary assertions.
3. **Your routing taste** — knowing which adopted runtime fits which job, applied with judgment.

Everything else is a layer somebody else has 50,000 to 300,000 stars working on. Adopt those. Compose them.

## Act III — The Synthesis

The architecture fell out of the reframe.

**Hermes** ([NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)) becomes the persistent orchestrator. Always-on. Slack, Telegram, voice, web — same agent, same memory, same skills. It saves successful approaches as reusable skills natively. It's MIT-licensed, model-agnostic, and growing 10,000 stars a month. Hermes isn't a "brain" — it's a brain *and* a flexible executor that decomposes work and routes the heavy parts to specialists.

**The specialist runtimes** are the tool belt:

- **OpenClaw** ([openclaw/openclaw](https://github.com/openclaw/openclaw)) — 302,000 stars. Autonomous shell, file, browser grind. When Hermes needs to run a 30-minute scrape-and-clean loop, this is the runtime.
- **browser-use** — structured browser automation. When the work is "navigate this site and extract this table."
- **Anthropic Computer Use SDK** — raw desktop, native apps.
- **Claude Code subagents** — interactive coding inside a repo.
- **Codex CLI** — background coding. Multi-provider hedge so a Claude outage doesn't stop the press.
- **Aider** — git-aware incremental commits.
- **Claude Managed Agents** — long-running cloud jobs.
- **E2B** — sandboxed code execution in clean VMs.
- **Exa** — neural search for "find me 10 articles about X."
- **LiveKit** — voice and realtime.
- **Terminal cron** — for the simple stuff.

Hermes routes per job tags. The default — for most work — is Hermes itself with sub-agent hierarchies. The specialists are *exceptions*, triggered when a job's shape demands them. This is the Nate Jones thesis in code: route by the shape of work.

**AGI-1** stays. It's the one piece that's uniquely Justin's. Vendored as a submodule. Auto-updated nightly to itself. When Justin ships a new council prompt or a sharper audit at 11pm, every running agent-os instance has it the next morning. Three skills exposed: `/agi-audit` (score), `/agi-council` (3-agent critique deliberation), `/agi-research` (Karpathy autoresearch — evolve prompts against binary assertions, promote winners that beat the incumbent by 5+ percentage points).

**The Vault** is a markdown directory tree, mirrored to Supabase. Every conversation. Every run artifact. Every incident. Every decision. Every skill. Every cross-project pattern that earned its way into the genome. Human-readable, grep-able, git-versionable, and the single source of truth no matter which channel a message came through.

**The manifest layer** is the bit nobody else's tooling does. Every component declares a `manifest.yaml`: who its agents are, what tools they use, what data they touch, what outputs they produce, who consumes them downstream. An aggregator walks the workspace nightly and builds a system graph. An MCP server exposes it. A `/explain` skill walks it conversationally. Now Justin can ask his own system "what wrote my morning brief?" or "how does the SDR fleet connect to the morning brief?" and get a real answer — a graph walk, not a guess.

**The upgrader daemon** is the secret sauce. Ten nightly streams. Each pulls upstream, runs a smoke test, promotes if green, quarantines if red. Hermes evolves with NousResearch. OpenClaw evolves with its 300K-star community. browser-use, Aider, agi-1, awesome-hermes-agent — all evolve every night. Justin's system gets the velocity of every contributor across every dependency for free. The wired-together, daily-evolving stack is the moat. Anyone can clone Hermes. Very few will run it tied to a daily-updating quality flywheel that's also pulling AGI-1 improvements every night.

**The accessibility layer** is what makes it a product instead of a tidier monorepo. Single-state guarantee: drop a file in Slack, ask about it on Telegram, voice-chat the answer in a web app — same Hermes, same memory, same context. One agent, one state, every channel.

**The four "self-" pillars** are explicit, with state machines, not vibes:

- **Self-healing** — the heartbeat detects (heartbeats, validators, cron, API health, cost), classifies against the genome, applies a known fix or spawns a 3-agent diagnostic council, verifies, and auto-promotes recurring fixes.
- **Self-learning** — every run writes binary assertions; nightly rollup detects plateau; `/agi-research` generates 5 variations; winner promotes.
- **Self-growing** — the upgrader pulls capabilities from upstream every night.
- **Self-skills** — Hermes saves successful approaches; agi-1 promotes high-confidence skills cross-project.

## Act IV — The Test

The product exists, or it doesn't, against five acceptance criteria:

1. *Same conversation, three channels.* Send "remember 42" via Slack. Ask via Telegram. Voice-chat the same question on the web app. All three return 42 with the same context.
2. *File context, cross-channel.* Drop a PDF in Slack. Ask about its contents from web app voice mode. Right answer.
3. *Streaming chat works.* Web app text streams tokens, doesn't wait for full response.
4. *Voice round-trip under 2 seconds* on a clean connection.
5. *One-command deploy.* Fresh checkout to full stack running.

If we hit those five, agent-os is a real product. Until we hit those five, it's scaffolding.

This commit is the scaffolding. The rest is execution.

## Why this won't drift back

Three structural defenses against the original pathology.

First, **never edit `vendor/`.** It's the unbreakable rule. Frustration with how Hermes handles X? Open an issue or a PR upstream. Frustration with OpenClaw? Same. The minute someone forks a vendored module locally, the upgrader breaks and the daily-evolution moat dies. So it's the bright line.

Second, **never start another framework wrapper.** New ideas go into a runtime adapter, a Hermes skill, or an upstream contribution. Period. The pathology was solo-rebuilding substrates that have ecosystem leaders. The discipline is to not do that anymore.

Third, **the monthly health check.** Total custom code (lines outside `vendor/`) holds flat or decreases month-over-month while shipped vertical apps in `examples/` increase. If custom LOC is climbing while shipped apps aren't, the drift is back. That's the leading indicator.

## Where we are

Repo: [github.com/jbellsolutions/agent-os](https://github.com/jbellsolutions/agent-os)

Skeleton committed. Vendored submodules pinned at:
- `hermes-agent` v2026.4.23
- `openclaw` v2026.4.19-beta.2
- `browser-use` 0.12.6
- `aider` v0.86.3.dev
- `agi-1` v2.2.1
- `awesome-hermes-agent` (latest)
- `nemoclaw` v0.0.24 (parked until NVIDIA marks GA)

Twenty-three tests pass. The CLI routes correctly. The manifest aggregator builds a 20-node, 57-edge graph from `manifest.yaml` files across the workspace. CI is wired. Deploy templates are ready. The `.claude/skills/` directory has seven entry-point skills.

The 14 old framework repos remain live, untouched, and silently archived in spirit. They were never the problem. They were the pattern. The pattern is broken now.

Now we build the thing.
