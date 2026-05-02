# Runbook: Agent Zero

## URL

<http://127.0.0.1:5080>

## Container

```bash
docker ps --filter name=agent-zero
docker logs --tail 100 agent-zero
docker restart agent-zero
docker stop agent-zero
docker start agent-zero
```

## Data path

```text
/Users/home/agent-zero/agent-zero/usr
```

## Config/env path

```text
/Users/home/agent-zero/agent-zero/usr/.env
```

## Verify health

```bash
curl -fsS -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:5080
```

Expected:

```text
HTTP 200
```

## Common fixes

### UI does not load

1. Check container:

```bash
docker ps --filter name=agent-zero
```

2. Restart:

```bash
docker restart agent-zero
```

3. Check logs:

```bash
docker logs --tail 120 agent-zero
```

### Docker/Colima not running

```bash
colima start
docker start agent-zero
```

### Agent Zero cannot access host Mac

Check A0 connector runbook.
