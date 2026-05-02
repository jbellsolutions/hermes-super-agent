# Fly.io deploy

```bash
fly launch --config deploy/fly/fly.toml
fly secrets set ANTHROPIC_API_KEY=... SLACK_BOT_TOKEN=... ...
fly deploy
```
