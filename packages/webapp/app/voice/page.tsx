"use client";
// TODO(stage-9): real LiveKit room + OpenAI Realtime / Gemini Realtime wiring.
// Reference: https://docs.livekit.io/agents/

export default function VoicePage() {
  return (
    <main style={{ padding: "2rem", maxWidth: 720, margin: "0 auto" }}>
      <h1>voice</h1>
      <p>LiveKit + OpenAI Realtime / Gemini Realtime.</p>
      <p><em>Stage 9 wiring TODO. Single-state guaranteed via the same /api/hermes that chat uses.</em></p>
      <button disabled>Connect (TODO)</button>
    </main>
  );
}
