# @agent-os/webapp

Next.js front-end. Two modes:

1. **Streaming text chat** (`/chat`) — WebSocket bridge to Hermes, drag-drop file upload.
2. **Two-way voice** (`/voice`) — LiveKit transport + OpenAI Realtime / Gemini Realtime.

Single-state guarantee: every message routes through `/api/hermes` which writes to
`vault/conversations/<user>.md` — same memory as Slack and Telegram.
