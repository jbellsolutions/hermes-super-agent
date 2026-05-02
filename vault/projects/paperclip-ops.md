# Project: paperclip-ops

## Type

DigitalOcean droplet / Paperclip operations candidate.

## Deployment

- Provider: DigitalOcean
- Droplet: `paperclip-ops`
- Region: `nyc1`
- Size: `s-2vcpu-4gb`
- Public IP: `167.172.131.251`
- Tags: `paperclip`, `operations`
- Status: `active`

## Why it matters

This was the strongest DigitalOcean candidate for a Paperclip operations/control-plane layer.

After Railway inspection, the strongest currently accessible Paperclip runtime appears to be Railway `agentstack-hermes`, not this droplet, because Railway exposes working Paperclip/Hermes services and public health endpoints.

## Current status

- Discovered via read-only DigitalOcean inventory.
- SSH attempted 2026-05-02 as `root`, `ubuntu`, and `justin`.
- Result: `Permission denied (publickey)` for all attempted users.
- Local SSH agent had no loaded identities.
- `~/.ssh/id_ed25519` exists locally but was not accepted by the droplet.
- No changes made.

## Approval rules

Requires Justin approval before:

- Adding SSH keys.
- Restarting services.
- Deploying code.
- Changing env vars.
- Scaling droplet.
- Deleting anything.
- Sending outbound messages from agents.

## Next read-only checks

Only continue when the correct SSH key is available or approved:

- SSH into host and identify:
  - running processes
  - Docker containers
  - systemd services
  - project directories
  - exposed ports
  - git remotes
  - log locations
- Map it to GitHub repo(s).
- Determine if it overlaps with Railway `agentstack-hermes` or is an older/stale Paperclip attempt.

## Current recommendation

Do not block the COO/Paperclip pilot on this droplet.

Focus first on:

1. Railway `coo-platform` for COO dashboard candidate.
2. Railway `agentstack-hermes` for active Paperclip/Hermes runtime.
3. Deployment health specialist as the first actual specialist-agent pilot.
