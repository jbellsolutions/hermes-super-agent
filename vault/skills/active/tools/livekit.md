---
name: livekit
runtime: livekit
tier: 2
category: voice_realtime
cost_class: medium
risk_class: low
preferred_models: [gpt-5.5, gemini-2.5-pro]
mcp_or_native: native
description: LiveKit + OpenAI Realtime API or Gemini Realtime API for voice/realtime conversations. Use when the task is voice-first or needs sub-2s round-trip audio.
---

## When to use
- Voice conversations with the user (web voice mode)
- Real-time transcription / live coaching during meetings
- Ultra-low-latency interactions where text-mode lag matters
- Customer demos that include voice as a channel

## When NOT to use
- Text-mode chat → hermes_self / channel adapters
- Async voice (speak now, hear later) → text + TTS instead
- Heavy synthesis tasks where latency doesn't matter → claude_subagents

## Alternatives (ordered)
1. **hermes_self** — for text-equivalent flows
2. **claude_managed** — for long async voice transcripts processed later

## Cost & latency
- Typical: $0.10/min (Realtime API)
- Round-trip: <2s on a clean connection
- Channel-handled — voice path joins the same Hermes pipeline

## Examples
- "Voice-chat through this onboarding flow"
- "Transcribe and summarize this live meeting in real time"
- "Demo voice mode to the customer"

## See also
- src/agent_os/runtimes/livekit/manifest.yaml
- ARCHITECTURE.md (voice path)
