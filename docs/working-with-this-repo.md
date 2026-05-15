# Working with this repo

Two remotes, one local clone, three scripts. Keep a private build log, push public-safe updates with confidence.

## The setup

This local clone has two remotes:

| Remote | URL | What's there |
|---|---|---|
| `origin` | github.com/jbellsolutions/hermes-super-agent | Public. Anyone can read. Sharable. |
| `internal` | github.com/jbellsolutions/hermes-super-agent-internal | Private. Only you. The working copy + your WORKLOG. |

Both remotes track the same `main` branch. The `internal` remote also keeps a `worklog` branch where your `WORKLOG.md` gets backed up automatically.

```bash
git remote -v
# origin    https://github.com/jbellsolutions/hermes-super-agent.git
# internal  https://github.com/jbellsolutions/hermes-super-agent-internal.git
```

## Daily workflow

### Log what you're doing as you go

```bash
./scripts/log.sh "tried adding Foo, broke on Bar"
./scripts/log.sh "fixed it by Baz"
./scripts/log.sh -                          # opens $EDITOR for a longer entry
```

Each call appends a timestamped entry to the top of `WORKLOG.md`. The file is gitignored — it lives only on your laptop and (after `publish.sh`) on the `internal` remote's `worklog` branch.

You can also tell Claude *"log what we just did"* and it'll run the script for you.

### Check what's leaking before you push

```bash
./scripts/safety-scan.sh             # scan the working tree
./scripts/safety-scan.sh --staged    # only scan what's staged for commit
./scripts/safety-scan.sh --history   # slow; scan all of git history
```

The scanner has ~25 patterns: API key prefixes, private-key headers, the 8 DigitalOcean IPs from the May 2026 cleanup, customer-tagged project names, internal email. If you onboard a new service or customer that shouldn't appear publicly, add the pattern to `SCAN_PATTERNS` in `scripts/safety-scan.sh`.

Exits 0 if clean, 1 if a leak is found. Wire it into a pre-commit hook if you want belt-and-suspenders:

```bash
# .git/hooks/pre-commit
#!/usr/bin/env bash
exec ./scripts/safety-scan.sh --staged
```

### Publish to public (and back up to private)

```bash
./scripts/publish.sh                # interactive — asks before pushing
./scripts/publish.sh --yes          # skip confirmation
./scripts/publish.sh --internal-only # only push to private (e.g. work-in-progress)
```

What it does, in order:

1. **Safety-scan the working tree.** Aborts if a leak pattern matches.
2. **Show what would be pushed.** Commits + file list + diff stat.
3. **Ask for confirmation** (unless `--yes`).
4. **Push `main` to `origin`** (public).
5. **Push `main` to `internal`** (private mirror).
6. **Back up `WORKLOG.md`** to `internal/worklog` branch as a separate commit — your build log is preserved across machines without ever touching public.

If `origin/main` has commits you don't have locally, the script tells you to `git pull --rebase origin main` first and aborts. Won't accidentally force-push.

## When to use which remote

- **Pushing to `origin` only** — work-in-progress that's already public-safe but not ready for the world. Use `git push origin main`.
- **Pushing to `internal` only** — private experiments, customer-specific configs, anything in your `vault/projects/` that the public should never see. Use `./scripts/publish.sh --internal-only`.
- **Pushing to both** — most days. Use `./scripts/publish.sh`.

## When you mess up

You committed a credential or a customer name. What now:

1. **Did you push yet?** If not: `git reset --soft HEAD~1`, fix the file, re-commit.
2. **Already pushed?** Do the cleanup dance:
   ```bash
   # Edit the file to remove the leak
   ./scripts/safety-scan.sh                      # confirm clean
   git filter-repo --replace-text /tmp/scrub.txt  # scrub from history
   git push --force origin main                   # overwrite public history
   ```
3. **Rotate the leaked credential.** History rewriting doesn't unleak data. If it was an API key, rotate it. If it was an IP, lock the firewall down.

Full incident playbook lives in your private WORKLOG of the May 2026 cleanup.

## Hygiene checklist

| | When |
|---|---|
| Run `./scripts/log.sh` | Whenever you try / fix / break something worth remembering |
| Run `./scripts/safety-scan.sh` | Before every commit (or wire it into a pre-commit hook) |
| Run `./scripts/publish.sh` | When you want to share work publicly |
| Run `./scripts/publish.sh --internal-only` | At end of day, to back up WORKLOG + private state |
| Add patterns to `safety-scan.sh` | When you onboard a new service / customer / IP / domain |

That's the whole workflow. ~3 commands, no branch-juggling, no manual file-by-file decisions.
