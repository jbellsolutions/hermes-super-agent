# Private Bootstrap Overlay

_Last updated: 2026-05-02_

## Purpose

Super Agent has two related setup modes:

1. **Public/commercial repo** — reusable functionality, docs, templates, setup flows, tool routing, vault sync contracts, and safe onboarding.
2. **Private internal overlay** — encrypted secrets, private profile defaults, personal agent templates, and private bootstrap scripts for a trusted owner/company.

The public repo must never contain raw secrets. The private overlay may contain encrypted secret bundles and company/private setup metadata, but it should still avoid committing plaintext `.env` files or raw SSH private keys.

## Recommended architecture

```text
jbellsolutions/hermes-super-agent            # public/product repo
  ├── docs
  ├── scripts
  ├── templates
  └── setup contracts

jbellsolutions/hermes-super-agent-private    # private/internal overlay
  ├── encrypted shared env bundle
  ├── encrypted optional private-file bundle
  ├── private agent templates
  └── scripts/create-agent.sh

Hermes profiles
  ├── primary/default
  ├── trading-agent
  ├── ***REMOVED***-coo
  ├── zions-agent
  └── paperclip-* agents
```

## Why use a private overlay instead of putting secrets in this repo?

Even private repos are easier to leak than people expect:

- accidental visibility changes
- cloned laptops
- compromised GitHub tokens
- CI logs
- copied repo zips
- agent mistakes
- broad collaborator access

The safer pattern is:

- public repo = everything reusable and sellable
- private repo = encrypted bootstrap overlay
- local/profile env = decrypted secrets at runtime only
- unique per-agent secrets collected during setup

## Owner/private flow

For Justin's internal agents, the private overlay can make a new agent feel nearly instant:

```bash
git clone https://github.com/jbellsolutions/hermes-super-agent-private.git
cd hermes-super-agent-private
./scripts/create-agent.sh trading-agent trading-agent
```

The private script should:

1. Verify `hermes`, `git`, and `age` are installed.
2. Clone or update the public Super Agent repo.
3. Create a Hermes profile for the new agent.
4. Decrypt the shared env bundle into the new profile.
5. Optionally restore encrypted private files such as SSH keys.
6. Apply a role template.
7. Ask only for unique per-agent secrets, usually Telegram bot token/chat.
8. Run `hermes --profile <name> doctor`.
9. Write a setup summary to Obsidian/Notion.

## What should be shared across private agents?

Shared, if the owner/company intentionally allows it:

- model/provider credentials
- GitHub credentials
- Railway/DigitalOcean inventory tokens
- Obsidian/Notion sync credentials
- common API connectors
- shared skills
- public repo setup contracts
- approval rules
- AGI/self-update/self-learning rules

Still unique per agent:

- Telegram bot token
- Telegram home channel/chat
- role/personality/heartbeat
- scoped project/company permissions
- trading/exchange execution keys
- customer-specific credentials
- outbound messaging permissions

## Trading-agent safety baseline

A trading or DCA agent should start with read-only/research permissions.

Allowed by default:

- market research
- DCA plan design
- backtesting
- portfolio reporting
- read-only exchange checks
- Obsidian/Notion reporting

Require explicit approval:

- live orders
- modifying a DCA bot
- withdrawals/transfers
- leverage/margin/futures/perps
- changing exchange API permissions
- unattended trading deployment

For production trading, use scoped exchange keys. Do not reuse broad master credentials.

## Commercial product version

The same concept becomes a customer/company secret-broker feature.

Commercial Super Agent should support:

- company-owned encrypted secret store
- role-scoped access policies
- per-agent profiles
- no plaintext secret exposure to end users/agents unless explicitly allowed
- audit log of which agent accessed which secret class and why
- approval gates for destructive actions, payments, trading, deployments, and outbound customer messages

Potential backends:

- 1Password Business
- Doppler
- Infisical
- Bitwarden/Vaultwarden
- HashiCorp Vault
- AWS Secrets Manager
- GCP Secret Manager
- Azure Key Vault
- GitHub Actions/Environments secrets for CI-only usage
- age/SOPS for simple owner-managed encrypted repo bundles

## Product UX goal

For an owner/company admin:

```text
Install Super Agent once.
Connect company secret store once.
Create role templates.
Spin up new agents in minutes.
Agents receive the access they need without seeing raw master credentials.
```

For an employee/role agent:

```text
Drop setup link.
Choose role.
Admin grants policy.
Agent gets scoped tools/secrets.
Agent logs actions to Obsidian/Notion/company dashboard.
```

## Sync rule between public and private repos

Public → private:

- new setup flows
- new tools
- changed env names
- new agent templates
- new vault/Notion schema
- changed routing/approval policy

Private → public:

- reusable non-secret setup patterns
- productized secret-broker docs
- generic scripts/templates
- lessons learned from internal agents

Never port private values, customer data, tokens, SSH keys, or decrypted env files back into the public repo.
