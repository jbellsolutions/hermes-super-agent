# Runbook: Codex

Codex is the coding execution engine.

## Verify

```bash
codex --version
```

Expected:

```text
codex-cli 0.125.0
```

## Paths

- Main binary: `/Users/home/.nvm/versions/node/v22.19.0/bin/codex`
- A0/Agent Zero wrapper: `/Users/home/.local/bin/codex`
- Auth file: `/Users/home/.codex/auth.json`

## Use from Hermes

Inside a git repo:

```bash
codex exec -s workspace-write 'Implement the requested change and run tests.'
```

For lower-friction sandboxed execution:

```bash
codex exec --full-auto 'Refactor this module and run tests.'
```

For review:

```bash
codex review --base origin/main
```

## Scratch smoke test

```bash
TMPDIR=$(mktemp -d /tmp/codex-smoke-XXXXXX)
cd "$TMPDIR"
git init -q
printf '# Codex smoke test\n' > README.md
git add README.md
git -c user.email=smoke@example.com -c user.name=Smoke commit -q -m 'init'
codex exec -s read-only --output-last-message "$TMPDIR/last.txt" 'Reply exactly: CODEX_READY' </dev/null
cat "$TMPDIR/last.txt"
```

Expected:

```text
CODEX_READY
```

## Best practice

Use git worktrees for real work:

```bash
git worktree add -b codex/my-task /tmp/codex-my-task main
cd /tmp/codex-my-task
codex exec --full-auto 'Task details here. Run tests and summarize changes.'
```
