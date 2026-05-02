# Agent OS Integration

We vendored and installed [Builder Methods Agent OS](https://github.com/buildermethods/agent-os) into this repo to add lightweight spec-driven-development workflows.

## Upstream source

- Upstream repo: `https://github.com/buildermethods/agent-os`
- Local clone: `/Users/home/agent-workspaces/upstream/agent-os`
- Vendored copy: `third_party/agent-os/`
- Upstream commit at import: `822af65 Improved discover-standards Q&A workflow`
- License: see `third_party/agent-os/LICENSE`

## What Agent OS adds

Agent OS is not another runtime. It is a **process/tooling layer** for better agent work:

- **Discover Standards** — Extract codebase conventions into concise standards.
- **Inject Standards** — Load relevant standards into an agent task context.
- **Shape Spec** — Turn a feature/change into a structured spec before implementation.
- **Index Standards** — Keep standards organized and discoverable.
- **Plan Product** — Create product mission, roadmap, and tech-stack docs.

## Installed files in this repo

The Agent OS project installer added:

```text
.claude/commands/agent-os/
├── discover-standards.md
├── index-standards.md
├── inject-standards.md
├── plan-product.md
└── shape-spec.md

agent-os/standards/index.yml
```

We also keep a vendored upstream copy at:

```text
third_party/agent-os/
```

## How we adapt it for Hermes Super Agent

Agent OS was written for Claude-style slash commands, but the workflow maps cleanly to Hermes/Codex/Agent Zero:

### Discover Standards

Use when onboarding any repo or project.

Hermes equivalent:

1. Inspect project structure.
2. Identify 3-5 areas where conventions matter.
3. Ask Justin which area to document.
4. Extract concise standards into `agent-os/standards/<area>/<standard>.md`.
5. Update `agent-os/standards/index.yml`.

### Inject Standards

Use before implementation.

Hermes equivalent:

1. Read `agent-os/standards/index.yml`.
2. Pick relevant standards for the current task.
3. Include them in the task brief for Hermes/Codex/Agent Zero.

### Shape Spec

Use before non-trivial code work.

Hermes equivalent:

1. Clarify the feature/change.
2. Gather visuals/references if any.
3. Read product docs and standards.
4. Create `agent-os/specs/YYYY-MM-DD-HHMM-feature-slug/` with:
   - `plan.md`
   - `shape.md`
   - `standards.md`
   - `references.md`
   - `visuals/`
5. Use Codex for implementation after spec approval.

### Plan Product

Use when starting a new product/repo.

Creates:

```text
agent-os/product/mission.md
agent-os/product/roadmap.md
agent-os/product/tech-stack.md
```

## macOS note

The upstream `project-install.sh` currently uses `tac`, which is not installed by default on macOS. The install still completed here, but it printed:

```text
tac: command not found
```

If we need a clean macOS-compatible install script, replace `tac` with `tail -r` on macOS or install GNU coreutils (`gtac`).

## Recommended workflow for code projects

1. Add Agent OS to the target repo.
2. Run standards discovery for the repo.
3. Create product docs if missing.
4. Shape a spec for each meaningful feature.
5. Pass the shaped spec to Codex in a git worktree.
6. Run tests/checks.
7. Update standards when new patterns emerge.
