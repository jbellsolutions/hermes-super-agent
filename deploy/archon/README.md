# Archon A2A Wrapper

Thin FastAPI shim that exposes Archon's agent-generation behind the A2A protocol so Hermes Admiral can delegate "build a specialist" jobs to it.

## Deploy

```bash
cd deploy/archon
railway init  # if not already
railway up
railway variables set ARCHON_BASE_URL=http://archon-internal:8100
```

Then on the Hermes Admiral side:
```bash
railway variables set ARCHON_A2A_URL=https://your-archon-wrapper.railway.app
```

## Stub mode

If `ARCHON_BASE_URL` is unreachable, the wrapper returns a minimal stub `AGENT.md` so the Tier 1 spawn pipeline can be tested end-to-end without a live Archon. Wire `_delegate_to_archon` in `wrapper.py` once you have Archon running.
