SDR fleet architecture DECIDED: Do NOT use delegate_task for autonomous SDRs. delegate_task is turn-bound — subagents die at end of inference cycle. 40 SDRs this way is impossible (3-child cap, max_spawn_depth=1). Architecture: dedicated SDR Super Agent profile (hermes profile create sdr-orchestrator), with SDR workers as separate long-lived hermes profiles. They share state via kanban.db or task queue. Report chain: SDR workers → SDR orchestrator → me.

§

Justin decided: create a standalone SDR Super Agent (separate hermes profile), not have me handle the sales fleet directly. Reason: scale, always-on state requirements, and separation of concerns. Justin will talk to the SDR orchestrator directly for sales ops.

§

Hermes subordinate agents: created via hermes profile create <name>, run as separate gateway processes or batch runners (tmux/systemd). NOT created via delegate_task. delegate_task = one-turn synchronous sub-tasks only. Long-lived autonomous agents must be separate profiles.
