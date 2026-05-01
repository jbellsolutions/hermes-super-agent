# Documentation Habit

Every meaningful stack change gets documented before it is considered done.

Update these files as appropriate:

- `docs/setup-log.md` — dated history of changes and smoke tests.
- `docs/inventory.md` — current tools, versions, paths, and capabilities.
- `docs/architecture.md` — how pieces connect.
- `docs/roadmap.md` — future work.
- `runbooks/*.md` — operational restart/fix instructions.
- `decisions/*.md` — architectural decisions and tradeoffs.

Commit after updating docs:

```bash
git add .
git commit -m "docs: describe change"
git push
```

If a workflow becomes reusable, turn it into a Hermes skill or an Agent OS standard.
