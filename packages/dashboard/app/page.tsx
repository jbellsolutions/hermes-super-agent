import fs from "node:fs";
import path from "node:path";

type FleetMember = {
  name: string;
  port: number | null;
  agency: string;
  business_purpose: string;
  customizer: string;
  live_status: string;
  last_run: string | null;
  started_at: string | null;
  cost_budget_daily_usd: number | null;
  cost_today_usd: number;
  runs_today: number;
};

type Snapshot = {
  generated_at: string;
  fleet: FleetMember[];
};

function loadSwarmSnapshot(): Snapshot | null {
  const vaultRoot = process.env.VAULT_ROOT || path.resolve(process.cwd(), "../..", "vault");
  const candidate = path.resolve(vaultRoot, "graph", "openswarm.json");
  try {
    return JSON.parse(fs.readFileSync(candidate, "utf8")) as Snapshot;
  } catch {
    return null;
  }
}

function statusColor(status: string): string {
  if (status === "running") return "#0a7d28";
  if (status === "starting-or-unhealthy") return "#b88500";
  if (status === "crashed") return "#a30000";
  return "#666";
}

export default function DashboardHome() {
  const snap = loadSwarmSnapshot();
  return (
    <main style={{ padding: "2rem", maxWidth: 1100, margin: "0 auto" }}>
      <h1>agent-os dashboard</h1>
      <p>Operator surface. TODO(post-stage-10): heartbeats, PendingActions, manifest graph viewer, upgrade reports, rollback.</p>
      <section>
        <h2>OpenSwarm fleet</h2>
        {snap === null ? (
          <pre>{`(no snapshot yet — run \`uv run python -c "from agent_os.runtimes.openswarm import fleet; fleet.snapshot_json()"\`)`}</pre>
        ) : snap.fleet.length === 0 ? (
          <pre>{`(no swarms registered — see vault/decisions/openswarm-runtime-adoption.md)`}</pre>
        ) : (
          <>
            <p style={{ fontSize: "0.85em", color: "#666" }}>
              Snapshot generated: {snap.generated_at}
            </p>
            <table style={{ borderCollapse: "collapse", width: "100%", fontSize: "0.9em" }}>
              <thead>
                <tr style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>
                  <th style={{ padding: "0.4rem" }}>Name</th>
                  <th style={{ padding: "0.4rem" }}>Status</th>
                  <th style={{ padding: "0.4rem" }}>Port</th>
                  <th style={{ padding: "0.4rem" }}>Customizer</th>
                  <th style={{ padding: "0.4rem" }}>Today</th>
                  <th style={{ padding: "0.4rem" }}>Last run</th>
                </tr>
              </thead>
              <tbody>
                {snap.fleet.map((s) => (
                  <tr key={s.name} style={{ borderBottom: "1px solid #f0f0f0" }}>
                    <td style={{ padding: "0.4rem", fontWeight: 600 }}>{s.name}</td>
                    <td style={{ padding: "0.4rem", color: statusColor(s.live_status) }}>
                      {s.live_status}
                    </td>
                    <td style={{ padding: "0.4rem" }}>{s.port ?? "-"}</td>
                    <td style={{ padding: "0.4rem" }}>{s.customizer}</td>
                    <td style={{ padding: "0.4rem" }}>
                      {s.runs_today} runs · ${s.cost_today_usd.toFixed(2)}
                      {s.cost_budget_daily_usd ? ` / $${s.cost_budget_daily_usd.toFixed(2)}` : ""}
                    </td>
                    <td style={{ padding: "0.4rem", color: "#666" }}>{s.last_run ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </section>
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
