# Runbook: A0 Connector

A0 Connector lets Agent Zero access the host Mac filesystem/shell.

## Current setup

- tmux session: `a0`
- launchd label: `com.justin.a0-connector`
- script: `/Users/home/bin/start-a0-connector.sh`
- plist: `/Users/home/Library/LaunchAgents/com.justin.a0-connector.plist`

## Inspect

```bash
tmux capture-pane -t a0 -p | tail -80
launchctl list | grep com.justin.a0-connector
```

## Attach manually

```bash
tmux attach -t a0
```

## Restart connector

```bash
tmux kill-session -t a0
launchctl unload ~/Library/LaunchAgents/com.justin.a0-connector.plist
launchctl load ~/Library/LaunchAgents/com.justin.a0-connector.plist
```

## Desired state

In the A0 UI footer:

```text
F3 Read&Write
F4 Code-exec ON
```

If it shows `Read-only`, press F3.
If it shows `Code-exec OFF`, press F4.

## Logs

```bash
tail -100 ~/Library/Logs/a0-connector.log
tail -100 ~/Library/Logs/a0-connector.err.log
```

## Verify Agent Zero can see host Codex

From Agent Zero, ask it to use `code_execution_remote` and run:

```bash
pwd && command -v codex && codex --version
```

Expected:

```text
/Users/home
/Users/home/.local/bin/codex
codex-cli 0.125.0
```
