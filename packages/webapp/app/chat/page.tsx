"use client";
import { useState } from "react";

export default function ChatPage() {
  const [messages, setMessages] = useState<{ role: string; text: string }[]>([]);
  const [input, setInput] = useState("");

  async function send() {
    const text = input.trim();
    if (!text) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    // TODO(stage-8): WebSocket stream to /api/hermes
    const r = await fetch("/api/hermes", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await r.json();
    setMessages((m) => [...m, { role: "assistant", text: data.reply }]);
  }

  return (
    <main style={{ padding: "2rem", maxWidth: 720, margin: "0 auto" }}>
      <h1>chat</h1>
      <div style={{ minHeight: 400, border: "1px solid #ddd", padding: 16, marginBottom: 12 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ margin: "8px 0" }}>
            <strong>{m.role}: </strong>
            {m.text}
          </div>
        ))}
      </div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && send()}
        placeholder="Drop a file or type — same conversation as Slack/Telegram"
        style={{ width: "100%", padding: 8, fontSize: 16 }}
      />
    </main>
  );
}
