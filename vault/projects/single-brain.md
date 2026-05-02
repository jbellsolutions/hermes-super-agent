# Project: single-brain

## Type

DigitalOcean droplet / COO Single Brain candidate.

## Deployment

- Provider: DigitalOcean
- Droplet: `single-brain`
- Droplet ID: `567676939`
- Region: `nyc3`
- Size: `s-2vcpu-4gb-intel`
- Disk: `80 GB`
- Image: Ubuntu 24.04 LTS x64
- Public IP: `104.236.11.200`
- Tags: `single-brain`
- Status: `active`

## Why it matters

Justin identified this as the closest current implementation of the desired COO concept: a single brand / single brain / business cofounder system running as another Hermes-style chat on a VPS.

The new COO should likely be rebuilt as the productized version of this idea, not as a patch to the old `coo-platform`.

## Current read-only findings

- DigitalOcean inventory confirms the droplet is active.
- Railway has no project named `single-brain`; the matching active Railway COO project is `coo-platform`.
- SSH attempted as `root`, `ubuntu`, and `justin`.
- SSH result: `Permission denied (publickey)` for all users.
- Public HTTP checks timed out on common ports:
  - `80`
  - `3000`
  - `8080`
  - `8000`
  - `5000`
- No changes made.

## Access blocker

The droplet exists, but we do not currently have an accepted SSH key loaded for it.

Options:

1. Load/provide the matching private key.
2. Add an approved public key to the droplet through DigitalOcean console/recovery flow.
3. Rebuild the COO from the Super Agent repo and use `single-brain` only as a reference if/when SSH access is restored.

## Current recommendation

Do not mutate or shut down `single-brain` yet.

Use it as the named target/concept for the new COO:

```text
Single Brain COO
  = Justin's business cofounder / COO / operating executive
  = separate clean business chat
  = reports to Justin and primary Hermes
  = controls Paperclip company teams once the registry and approval gates are ready
```

## Approval rules

Requires Justin approval before:

- Adding SSH keys.
- Restarting services.
- Stopping/shutting down droplet.
- Rebuilding in place.
- Repointing DNS/domains.
- Moving credentials or data.

## Next safe steps

1. Restore SSH access or confirm we should rebuild on a new clean VPS/Railway project.
2. Create a new COO source repo or refresh `jbellsolutions/coo-agent` with the new Super Agent architecture.
3. Define the COO identity, authority, reporting cadence, business decision rights, and approval gates.
4. Connect COO to the portfolio registry and Paperclip adapter after the deployment health specialist is stable.
