import { ShieldCheck, ShieldX, AlertTriangle, User } from "lucide-react";

function StatusPill({ status }) {
  const map = {
    PASS: { bg: "var(--color-risk-low-soft)", fg: "var(--color-risk-low)", label: "PASS" },
    RESOLVES: { bg: "var(--color-bg-sunken)", fg: "var(--color-text-tertiary)", label: "RESOLVES" },
    FAIL: { bg: "var(--color-risk-high-soft)", fg: "var(--color-risk-high)", label: "FAIL" },
    UNKNOWN: { bg: "var(--color-bg-sunken)", fg: "var(--color-text-tertiary)", label: "UNKNOWN" },
    SUSPICIOUS: { bg: "var(--color-risk-medium-soft)", fg: "var(--color-risk-medium)", label: "SUSPICIOUS" },
  };
  const s = map[status] || map.UNKNOWN;
  return (
    <span
      className="rounded px-2 py-0.5 text-[10px] font-mono font-semibold"
      style={{ backgroundColor: s.bg, color: s.fg }}
    >
      {s.label}
    </span>
  );
}

function Row({ label, value, status }) {
  return (
    <div className="flex items-center justify-between py-2 border-b last:border-0">
      <span className="text-xs" style={{ color: "var(--color-text-secondary)" }}>{label}</span>
      <div className="flex items-center gap-2">
        {value && (
          <span className="text-xs font-mono max-w-[200px] truncate" style={{ color: "var(--color-text-primary)" }}>
            {value}
          </span>
        )}
        {status && <StatusPill status={status} />}
      </div>
    </div>
  );
}

export default function SenderVerification({ sender }) {
  if (!sender) return null;

  const isSuspicious = sender.typosquatted || sender.spf === "FAIL" || sender.dkim === "FAIL";

  return (
    <div className="rounded-2xl border p-5" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
      <div className="flex items-center gap-2 mb-4">
        <User size={15} style={{ color: "var(--color-accent)" }} />
        <span className="text-xs font-mono uppercase tracking-wide" style={{ color: "var(--color-text-tertiary)" }}>
          Sender verification
        </span>
        {isSuspicious
          ? <ShieldX size={14} style={{ color: "var(--color-risk-high)" }} />
          : <ShieldCheck size={14} style={{ color: "var(--color-risk-low)" }} />
        }
      </div>

      <div className="space-y-0">
        <Row label="From" value={sender.from} />
        <Row label="Display name" value={sender.displayName} />
        {sender.replyTo && <Row label="Reply-To" value={sender.replyTo} status={sender.replyTo !== sender.from ? "SUSPICIOUS" : "PASS"} />}
        <Row label="Domain" value={sender.domain} status={sender.typosquatted ? "SUSPICIOUS" : "RESOLVES"} />
        <Row label="SPF" status={sender.spf} />
        <Row label="DKIM" status={sender.dkim} />
        <Row label="DMARC" status={sender.dmarc} />
        {sender.domainAgeDays != null && (
          <Row
            label="Domain age"
            value={sender.domainAgeDays < 30 ? `${sender.domainAgeDays} days — newly registered` : `${sender.domainAgeDays} days`}
            status={sender.domainAgeDays < 30 ? "SUSPICIOUS" : "PASS"}
          />
        )}
      </div>

      {sender.typosquatted && (
        <div
          className="mt-4 flex items-start gap-2 rounded-lg p-3 text-xs"
          style={{ backgroundColor: "var(--color-risk-medium-soft)", color: "var(--color-risk-medium)" }}
        >
          <AlertTriangle size={13} className="mt-0.5 shrink-0" />
          Typosquatting detected: domain closely resembles a trusted brand but contains character substitutions.
        </div>
      )}
    </div>
  );
}
