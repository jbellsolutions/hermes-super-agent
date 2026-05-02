export default function DashboardHome() {
  return (
    <main style={{ padding: "2rem", maxWidth: 1100, margin: "0 auto" }}>
      <h1>agent-os dashboard</h1>
      <p>Operator surface. TODO(post-stage-10): heartbeats, PendingActions, manifest graph viewer, upgrade reports, rollback.</p>
      <section>
        <h2>Heartbeats</h2>
        <pre>{`(reads from vault/heartbeats/)`}</pre>
      </section>
      <section>
        <h2>Recent upgrades</h2>
        <pre>{`(reads from vault/upgrades/)`}</pre>
      </section>
      <section>
        <h2>System graph</h2>
        <pre>{`(reads from vault/graph/system.yaml — manifest aggregator output)`}</pre>
      </section>
    </main>
  );
}
