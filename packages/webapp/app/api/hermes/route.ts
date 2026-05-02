// Web channel API route — hands incoming messages to the Hermes orchestrator.
// Single-state guarantee: the Python channels.web handler appends to
// vault/conversations/<user>.md, the same file Slack/Telegram write to.

export async function POST(req: Request) {
  const { text } = (await req.json()) as { text: string };
  // TODO(stage-8): proxy to a Python service exposing channels.web.handler.on_message
  //                e.g. via FastAPI/uvicorn at HERMES_BRIDGE_URL.
  const reply = `(stub web reply for: ${text.slice(0, 80)})`;
  return Response.json({ reply });
}
