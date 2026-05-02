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

This is the strongest DigitalOcean candidate for the Paperclip operations/control-plane layer. It may be running or intended to run the dashboard/agent-company infrastructure Justin wants for autonomous businesses.

## Current status

- Discovered via read-only DigitalOcean inventory.
- Not yet SSH-inspected.
- No changes made.

## Approval rules

Requires Justin approval before:

- Restarting services.
- Deploying code.
- Changing env vars.
- Scaling droplet.
- Deleting anything.
- Sending outbound messages from agents.

## Next read-only checks

- SSH into host and identify:
  - running processes
  - Docker containers
  - systemd services
  - project directories
  - exposed ports
  - git remotes
  - log locations
- Map it to GitHub repo(s).
- Determine if it can report heartbeat/status to primary Hermes.
