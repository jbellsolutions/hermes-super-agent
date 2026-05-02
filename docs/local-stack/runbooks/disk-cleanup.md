# Runbook: Disk Cleanup

## Check disk

```bash
df -h / /Users/home
```

## Safe cache cleanup

```bash
brew cleanup -s --prune=all || true
npm cache clean --force || true
rm -rf ~/.npm/_cacache ~/.npm/_logs ~/.npm/_npx
rm -rf ~/.cache/pip ~/Library/Caches/pip ~/.cache/uv ~/Library/Caches/uv
rm -rf ~/Library/Caches/Homebrew/downloads/*
rm -rf ~/Library/Logs/*
rm -rf ~/Library/Caches/*
rm -rf ~/Library/Application\ Support/CrashReporter/*
rm -rf ~/Library/Developer/Xcode/DerivedData/*
rm -rf ~/Library/Developer/CoreSimulator/Caches/*
rm -rf ~/.Trash/*
```

## Local Time Machine snapshots

List:

```bash
tmutil listlocalsnapshots /
```

Delete a snapshot:

```bash
tmutil deletelocalsnapshots YYYY-MM-DD-HHMMSS
```

## Video cleanup note

On 2026-05-01, downloaded/local videos in Desktop, Downloads, Documents, and Movies were removed per Justin's approval. A local Time Machine snapshot had to be deleted before free space appeared.

## Warning

Do not delete:

- `~/.hermes`
- `~/.codex`
- `/Users/home/agent-zero`
- project repos
- credential/auth files
