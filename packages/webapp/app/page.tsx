export default function Home() {
  return (
    <main style={{ padding: "2rem", maxWidth: 720, margin: "0 auto" }}>
      <h1>agent-os</h1>
      <p>One agent. One state. Every channel.</p>
      <ul>
        <li><a href="/chat">Streaming text chat</a></li>
        <li><a href="/voice">Two-way voice (LiveKit)</a></li>
      </ul>
    </main>
  );
}
