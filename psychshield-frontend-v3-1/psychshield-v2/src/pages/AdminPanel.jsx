import { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from "recharts";
import { ListChecks, Users, Activity, Loader2 } from "lucide-react";
import { api } from "../lib/api";
import { mockUsers, mockModelMetrics, TRIGGER_META } from "../lib/mockData";

function formatTimestamp(iso) {
  return new Date(iso).toLocaleString(undefined, {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

function MetricCard({ label, value, unit, target, good }) {
  const isGood = good(value);
  return (
    <div className="rounded-xl border p-4" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
      <p className="text-[11px] font-mono uppercase tracking-wide mb-2" style={{ color: "var(--color-text-tertiary)" }}>
        {label}
      </p>
      <p className="text-2xl font-bold font-mono" style={{ color: isGood ? "var(--color-risk-low)" : "var(--color-risk-high)" }}>
        {value}{unit}
      </p>
      <p className="text-[11px] mt-1" style={{ color: "var(--color-text-tertiary)" }}>
        Target: {target}
      </p>
    </div>
  );
}

export default function AdminPanel() {
  const triggerColorKeys = ["urgency", "fear", "authority", "trust", "pity"];
  const [analytics, setAnalytics] = useState(null);
  const [auditLog, setAuditLog] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getAnalytics(), api.getAuditLog()])
      .then(([analyticsData, auditData]) => {
        setAnalytics(analyticsData || {});
        setAuditLog(auditData || []);
      })
      .catch((err) => console.error("Admin load error:", err))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 size={24} className="animate-spin" style={{ color: "var(--color-accent)" }} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <div className="mb-8">
        <p className="text-xs font-mono uppercase tracking-wide" style={{ color: "var(--color-accent)" }}>
          Admin panel
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight" style={{ color: "var(--color-text-primary)" }}>
          Organization-wide monitoring
        </h1>
        <p className="mt-2 max-w-2xl text-sm" style={{ color: "var(--color-text-secondary)" }}>
          Aggregate trigger frequency, model performance, user management, and system audit history.
        </p>
      </div>

      {/* Model performance metrics */}
      <section className="mb-8">
        <div className="flex items-center gap-2 mb-4">
          <Activity size={15} style={{ color: "var(--color-accent)" }} />
          <h2 className="text-sm font-semibold" style={{ color: "var(--color-text-primary)" }}>
            Model performance
          </h2>
          <span className="text-[11px] font-mono" style={{ color: "var(--color-text-tertiary)" }}>
            Last evaluated: {formatTimestamp(mockModelMetrics.lastEvaluated)}
          </span>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard label="Overall accuracy" value={mockModelMetrics.accuracy} unit="%" target="≥ 90%" good={(v) => v >= 90} />
          <MetricCard label="HIGH-tier recall" value={mockModelMetrics.highRecall} unit="%" target="≥ 92%" good={(v) => v >= 92} />
          <MetricCard label="Precision" value={mockModelMetrics.precision} unit="%" target="≥ 88%" good={(v) => v >= 88} />
          <MetricCard label="Avg latency" value={(mockModelMetrics.avgLatencyMs / 1000).toFixed(2)} unit="s" target="≤ 3s" good={(v) => v <= 3} />
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-[1fr_1fr] mb-6">
        {/* Top triggers chart */}
        <div className="rounded-2xl border p-5" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
          <p className="text-xs font-mono uppercase tracking-wide mb-4" style={{ color: "var(--color-text-tertiary)" }}>
            Most frequent triggers (org-wide)
          </p>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={analytics?.topTriggers || []} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: "var(--color-text-tertiary)" }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="trigger" tick={{ fontSize: 12, fill: "var(--color-text-secondary)" }} axisLine={false} tickLine={false} width={80} />
              <Tooltip contentStyle={{ backgroundColor: "var(--color-bg-elevated)", border: "1px solid var(--color-border-strong)", borderRadius: 8, fontSize: 12 }} />
              <Bar dataKey="count" radius={[0, 6, 6, 0]}>
                {(analytics?.topTriggers || []).map((entry, i) => (
                  <Cell key={entry.trigger} fill={`var(${TRIGGER_META[triggerColorKeys[i]]?.colorVar})`} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Audit log */}
        <div className="rounded-2xl border p-5" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
          <div className="flex items-center gap-2 mb-4">
            <ListChecks size={15} style={{ color: "var(--color-accent)" }} />
            <p className="text-xs font-mono uppercase tracking-wide" style={{ color: "var(--color-text-tertiary)" }}>
              Audit log
            </p>
          </div>
          <div className="space-y-3 max-h-[240px] overflow-y-auto">
            {auditLog.map((log) => (
              <div key={log.id} className="text-sm border-b pb-3 last:border-0 last:pb-0">
                <p style={{ color: "var(--color-text-primary)" }}>{log.action}</p>
                <div className="mt-1 flex items-center gap-2 text-xs font-mono" style={{ color: "var(--color-text-tertiary)" }}>
                  <span>{log.actor}</span>
                  <span>·</span>
                  <span>{formatTimestamp(log.timestamp)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* User management */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Users size={15} style={{ color: "var(--color-accent)" }} />
          <h2 className="text-sm font-semibold" style={{ color: "var(--color-text-primary)" }}>
            User management
          </h2>
        </div>
        <div className="rounded-2xl border divide-y" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
          {/* Table header */}
          <div className="grid grid-cols-[1fr_140px_100px_80px] gap-4 px-5 py-3 text-[11px] font-mono uppercase tracking-wide" style={{ color: "var(--color-text-tertiary)" }}>
            <span>User</span>
            <span>Last login</span>
            <span>Role</span>
            <span>Status</span>
          </div>
          {mockUsers.map((user) => (
            <div key={user.id} className="grid grid-cols-[1fr_140px_100px_80px] gap-4 px-5 py-4 items-center">
              <div>
                <p className="text-sm font-medium" style={{ color: "var(--color-text-primary)" }}>{user.name}</p>
                <p className="text-xs font-mono" style={{ color: "var(--color-text-tertiary)" }}>{user.email}</p>
              </div>
              <span className="text-xs font-mono" style={{ color: "var(--color-text-tertiary)" }}>
                {formatTimestamp(user.lastLogin)}
              </span>
              <span
                className="inline-flex w-fit rounded-md px-2 py-0.5 text-[11px] font-mono font-semibold capitalize"
                style={{
                  backgroundColor: user.role === "admin" ? "var(--color-accent-soft)" : "var(--color-bg-sunken)",
                  color: user.role === "admin" ? "var(--color-accent)" : "var(--color-text-secondary)",
                }}
              >
                {user.role}
              </span>
              <span
                className="inline-flex w-fit rounded-md px-2 py-0.5 text-[11px] font-mono font-semibold"
                style={{
                  backgroundColor: "var(--color-risk-low-soft)",
                  color: "var(--color-risk-low)",
                }}
              >
                {user.status}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
