import { useState, useEffect } from "react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { Inbox, ShieldCheck, ShieldAlert, ShieldX, Loader2, Download } from "lucide-react";
import RiskBadge from "../components/ui/RiskBadge";
import { api, downloadReport } from "../lib/api";
import ScrollReveal from "../components/ui/ScrollReveal";

const TIER_FILTERS = ["All", "High", "Medium", "Low"];

function StatCard({ icon: Icon, label, value, colorVar }) {
  return (
    <div className="rounded-2xl border p-5" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono uppercase tracking-wide" style={{ color: "var(--color-text-tertiary)" }}>
          {label}
        </span>
        <Icon size={16} style={{ color: `var(${colorVar})` }} />
      </div>
      <p className="mt-3 text-2xl font-bold font-mono" style={{ color: "var(--color-text-primary)" }}>
        {(value ?? 0).toLocaleString()}
      </p>
    </div>
  );
}

export default function Dashboard() {
  const [filter, setFilter] = useState("All");
  const [emails, setEmails] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getEmails(), api.getAnalytics()])
      .then(([emailData, analyticsData]) => {
        setEmails(emailData || []);
        setAnalytics(analyticsData || {});
      })
      .catch((err) => console.error("Dashboard load error:", err))
      .finally(() => setIsLoading(false));
  }, []);

  const filteredEmails = filter === "All" ? emails : emails.filter((e) => e.riskTier === filter);

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
          Dashboard
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight" style={{ color: "var(--color-text-primary)" }}>
          Risk-labeled inbox overview
        </h1>
      </div>

      {/* Stat cards */}
      <ScrollReveal>
      <div className="grid gap-4 sm:grid-cols-4">
        <StatCard icon={Inbox} label="Total analyzed" value={analytics?.totalAnalyzed} colorVar="--color-accent" />
        <StatCard icon={ShieldX} label="High risk" value={analytics?.highRisk} colorVar="--color-risk-high" />
        <StatCard icon={ShieldAlert} label="Medium risk" value={analytics?.mediumRisk} colorVar="--color-risk-medium" />
        <StatCard icon={ShieldCheck} label="Low risk" value={analytics?.lowRisk} colorVar="--color-risk-low" />
      </div>
      </ScrollReveal>

      {/* Trend chart */}
      <ScrollReveal delay={0.1}>
      <div className="mt-6 rounded-2xl border p-5" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
        <p className="text-xs font-mono uppercase tracking-wide mb-4" style={{ color: "var(--color-text-tertiary)" }}>
          7-day detection trend
        </p>
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={analytics?.detectionRateTrend || []}>
            <defs>
              <linearGradient id="highGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--color-risk-high)" stopOpacity={0.35} />
                <stop offset="100%" stopColor="var(--color-risk-high)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
            <XAxis dataKey="date" tick={{ fontSize: 11, fill: "var(--color-text-tertiary)" }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: "var(--color-text-tertiary)" }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--color-bg-elevated)",
                border: "1px solid var(--color-border-strong)",
                borderRadius: 8,
                fontSize: 12,
              }}
            />
            <Area type="monotone" dataKey="high" stroke="var(--color-risk-high)" fill="url(#highGrad)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      </ScrollReveal>

      {/* Download reports */}
      <ScrollReveal delay={0.15}>
      <div className="mt-6 rounded-2xl border p-5" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
        <div className="flex items-center gap-2 mb-4">
          <Download size={15} style={{ color: "var(--color-accent)" }} />
          <p className="text-xs font-mono uppercase tracking-wide" style={{ color: "var(--color-text-tertiary)" }}>
            Download analysis reports
          </p>
        </div>
        <p className="text-xs mb-4" style={{ color: "var(--color-text-secondary)" }}>
          Export a CSV report of all emails you have analyzed within the selected period.
        </p>
        <div className="flex flex-wrap gap-3">
          {[
            { label: "Weekly report", period: "weekly", desc: "Last 7 days" },
            { label: "Monthly report", period: "monthly", desc: "Last 30 days" },
            { label: "Yearly report", period: "yearly", desc: "Last 365 days" },
          ].map((r) => (
            <button
              key={r.period}
              onClick={() => downloadReport(r.period).catch((e) => console.error("Download error:", e))}
              className="focus-ring inline-flex items-center gap-2 rounded-lg border px-4 py-2.5 text-sm font-medium transition-colors hover:opacity-80"
              style={{ borderColor: "var(--color-border-strong)", color: "var(--color-text-primary)" }}
            >
              <Download size={14} style={{ color: "var(--color-accent)" }} />
              <span>{r.label}</span>
              <span className="text-[10px] font-mono" style={{ color: "var(--color-text-tertiary)" }}>
                ({r.desc})
              </span>
            </button>
          ))}
        </div>
      </div>
      </ScrollReveal>

      {/* Email list */}
      <ScrollReveal delay={0.2}>
      <div className="mt-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold" style={{ color: "var(--color-text-primary)" }}>
            Recent emails
          </h2>
          <div className="flex gap-1">
            {TIER_FILTERS.map((tier) => (
              <button
                key={tier}
                onClick={() => setFilter(tier)}
                className="focus-ring rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
                style={{
                  backgroundColor: filter === tier ? "var(--color-accent-soft)" : "transparent",
                  color: filter === tier ? "var(--color-accent)" : "var(--color-text-secondary)",
                }}
              >
                {tier}
              </button>
            ))}
          </div>
        </div>

        {filteredEmails.length > 0 ? (
          <div className="rounded-2xl border divide-y" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
            {filteredEmails.map((email) => (
              <div
                key={email.id}
                className="p-4 first:rounded-t-2xl last:rounded-b-2xl"
                style={{
                  borderLeft: email.riskTier === "High"
                    ? "4px solid var(--color-risk-high)"
                    : email.riskTier === "Medium"
                    ? "4px solid var(--color-risk-medium)"
                    : "4px solid var(--color-risk-low)",
                }}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate" style={{ color: "var(--color-text-primary)" }}>
                      {email.subject || email.snippet?.substring(0, 80) || "No subject"}
                    </p>
                    <p
                      className="text-xs font-mono mt-1 break-all"
                      style={{
                        color: email.riskTier === "High"
                          ? "var(--color-risk-high)"
                          : "var(--color-text-tertiary)",
                      }}
                    >
                      {email.sender || "Unknown sender"}
                    </p>
                    <p className="text-xs mt-1 line-clamp-2" style={{ color: "var(--color-text-secondary)" }}>
                      {email.snippet}
                    </p>
                    {email.riskTier === "High" && (
                      <div className="mt-2 flex items-center gap-2">
                        <span
                          className="rounded px-2 py-0.5 text-[10px] font-mono font-semibold"
                          style={{
                            backgroundColor: "var(--color-risk-high-soft)",
                            color: "var(--color-risk-high)",
                          }}
                        >
                          INVESTIGATION REQUIRED
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="flex flex-col items-end gap-1 shrink-0">
                    <RiskBadge tier={email.riskTier} score={email.riskScore} size="sm" />
                    <span className="text-[10px] font-mono" style={{ color: "var(--color-text-tertiary)" }}>
                      {email.receivedAt
                        ? new Date(email.receivedAt).toLocaleString(undefined, {
                            month: "short",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          })
                        : ""}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border p-8 text-center" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
            <p className="text-sm" style={{ color: "var(--color-text-tertiary)" }}>
              No emails analyzed yet. Go to the Analysis page to scan an email.
            </p>
          </div>
        )}
      </div>
      </ScrollReveal>
    </div>
  );
}
