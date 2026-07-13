import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ScanLine, Loader2, AlertTriangle, ChevronDown, ChevronUp, ShieldAlert, ShieldCheck, Shield } from "lucide-react";
import { api } from "../../lib/api";

const TIER_STYLES = {
  High:   { border: "var(--color-risk-high)",   bg: "var(--color-risk-high-soft)",   text: "var(--color-risk-high)",   icon: ShieldAlert },
  Medium: { border: "var(--color-risk-medium)", bg: "var(--color-risk-medium-soft)", text: "var(--color-risk-medium)", icon: Shield },
  Low:    { border: "var(--color-risk-low)",    bg: "var(--color-risk-low-soft)",    text: "var(--color-risk-low)",    icon: ShieldCheck },
};

function ResultRow({ result }) {
  const [expanded, setExpanded] = useState(false);
  const style = TIER_STYLES[result.riskTier] || TIER_STYLES.Low;
  const Icon = style.icon;

  return (
    <div
      className="rounded-xl border-l-4 overflow-hidden"
      style={{ borderColor: style.border, backgroundColor: "var(--color-bg-elevated)" }}
    >
      {/* Summary row — always visible */}
      <button
        onClick={() => setExpanded((p) => !p)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left"
      >
        <Icon size={16} style={{ color: style.text, flexShrink: 0 }} />

        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate" style={{ color: "var(--color-text-primary)" }}>
            {result.subject}
          </p>
          <p className="text-xs truncate mt-0.5" style={{ color: "var(--color-text-tertiary)" }}>
            {result.senderAddr || result.sender} · {result.date ? new Date(result.date).toLocaleDateString() : "—"}
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span
            className="rounded-full px-2.5 py-0.5 text-xs font-bold tabular-nums"
            style={{ backgroundColor: style.bg, color: style.text }}
          >
            {result.riskScore}
          </span>
          <span className="text-xs font-semibold" style={{ color: style.text }}>
            {result.riskTier}
          </span>
          {expanded
            ? <ChevronUp size={14} style={{ color: "var(--color-text-tertiary)" }} />
            : <ChevronDown size={14} style={{ color: "var(--color-text-tertiary)" }} />
          }
        </div>
      </button>

      {/* Expanded detail */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div
              className="px-4 pb-4 pt-1 space-y-3 border-t"
              style={{ borderColor: "var(--color-border)" }}
            >
              {/* Explanation */}
              <p className="text-xs leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
                {result.explanation}
              </p>

              {/* Score reason override badge */}
              {result.scoreReason && (
                <div
                  className="flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium"
                  style={{ backgroundColor: style.bg, color: style.text }}
                >
                  <AlertTriangle size={11} />
                  {result.scoreReason}
                </div>
              )}

              {/* Trigger breakdown */}
              {result.triggers && (
                <div className="space-y-1.5">
                  <p className="text-[10px] font-mono uppercase tracking-wide" style={{ color: "var(--color-text-tertiary)" }}>
                    Psychological triggers
                  </p>
                  {Object.entries(result.triggers).map(([key, val]) => (
                    <div key={key} className="flex items-center gap-2">
                      <span className="text-xs w-16 capitalize" style={{ color: "var(--color-text-secondary)" }}>{key}</span>
                      <div className="flex-1 h-1.5 rounded-full" style={{ backgroundColor: "var(--color-bg-sunken)" }}>
                        <div
                          className="h-1.5 rounded-full transition-all"
                          style={{
                            width: `${Math.min(val, 100)}%`,
                            backgroundColor: val > 60 ? "var(--color-risk-high)" : val > 30 ? "var(--color-risk-medium)" : "var(--color-risk-low)",
                          }}
                        />
                      </div>
                      <span className="text-xs tabular-nums w-8 text-right" style={{ color: "var(--color-text-tertiary)" }}>
                        {val}%
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Link reason */}
              {result.linkReason && (
                <p className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>
                  {result.linkReason}
                </p>
              )}

              {/* Snippet */}
              <div className="rounded-lg p-3" style={{ backgroundColor: "var(--color-bg-sunken)" }}>
                <p className="text-[10px] font-mono uppercase tracking-wide mb-1" style={{ color: "var(--color-text-tertiary)" }}>
                  Preview
                </p>
                <p className="text-xs leading-relaxed line-clamp-4" style={{ color: "var(--color-text-secondary)" }}>
                  {result.snippet}
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function SummaryBar({ total, high, medium, low }) {
  return (
    <div className="grid grid-cols-3 gap-3">
      {[
        { label: "High Risk", count: high, color: "var(--color-risk-high)", bg: "var(--color-risk-high-soft)" },
        { label: "Medium Risk", count: medium, color: "var(--color-risk-medium)", bg: "var(--color-risk-medium-soft)" },
        { label: "Low Risk", count: low, color: "var(--color-risk-low)", bg: "var(--color-risk-low-soft)" },
      ].map(({ label, count, color, bg }) => (
        <div
          key={label}
          className="rounded-xl p-3 text-center"
          style={{ backgroundColor: bg }}
        >
          <p className="text-2xl font-bold tabular-nums" style={{ color }}>{count}</p>
          <p className="text-[10px] font-semibold uppercase tracking-wide mt-0.5" style={{ color }}>{label}</p>
        </div>
      ))}
    </div>
  );
}

/**
 * GmailScanPanel
 * --------------
 * Controls for scanning the Gmail inbox and displaying results.
 * Only rendered when Gmail is connected.
 */
export default function GmailScanPanel() {
  const [maxResults, setMaxResults] = useState(20);
  const [daysBack, setDaysBack] = useState(7);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState(null);

  async function handleScan() {
    setScanning(true);
    setError(null);
    setScanResult(null);
    try {
      const data = await api.gmailScan({ max_results: maxResults, days_back: daysBack, unread_only: unreadOnly });
      setScanResult(data);
    } catch (err) {
      if (err.status === 401) {
        setError("Gmail access was revoked. Please disconnect and reconnect your account.");
      } else {
        setError(err.message || "Scan failed. Try again.");
      }
    } finally {
      setScanning(false);
    }
  }

  return (
    <div className="space-y-5">
      {/* Scan controls */}
      <div
        className="rounded-2xl border p-5 space-y-4"
        style={{ backgroundColor: "var(--color-bg-elevated)" }}
      >
        <p className="text-xs font-mono uppercase tracking-wide" style={{ color: "var(--color-text-tertiary)" }}>
          Scan settings
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {/* Max results */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium" style={{ color: "var(--color-text-secondary)" }}>
              Emails to scan
            </label>
            <select
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
              className="w-full rounded-xl px-3 py-2 text-sm border"
              style={{
                backgroundColor: "var(--color-bg-sunken)",
                color: "var(--color-text-primary)",
                borderColor: "var(--color-border)",
              }}
            >
              {[10, 20, 30, 50].map((n) => (
                <option key={n} value={n}>{n} emails</option>
              ))}
            </select>
          </div>

          {/* Days back */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium" style={{ color: "var(--color-text-secondary)" }}>
              Time range
            </label>
            <select
              value={daysBack}
              onChange={(e) => setDaysBack(Number(e.target.value))}
              className="w-full rounded-xl px-3 py-2 text-sm border"
              style={{
                backgroundColor: "var(--color-bg-sunken)",
                color: "var(--color-text-primary)",
                borderColor: "var(--color-border)",
              }}
            >
              {[{ v: 1, l: "Last 24 hours" }, { v: 7, l: "Last 7 days" }, { v: 14, l: "Last 14 days" }, { v: 30, l: "Last 30 days" }, { v: 90, l: "Last 90 days" }].map(({ v, l }) => (
                <option key={v} value={v}>{l}</option>
              ))}
            </select>
          </div>

          {/* Unread only */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium" style={{ color: "var(--color-text-secondary)" }}>
              Filter
            </label>
            <button
              onClick={() => setUnreadOnly((p) => !p)}
              className="w-full rounded-xl px-3 py-2 text-sm border flex items-center gap-2"
              style={{
                backgroundColor: unreadOnly ? "var(--color-accent-soft, var(--color-bg-sunken))" : "var(--color-bg-sunken)",
                color: unreadOnly ? "var(--color-accent)" : "var(--color-text-secondary)",
                borderColor: unreadOnly ? "var(--color-accent)" : "var(--color-border)",
              }}
            >
              <span
                className="w-3.5 h-3.5 rounded border flex items-center justify-center shrink-0"
                style={{ borderColor: unreadOnly ? "var(--color-accent)" : "var(--color-border)", backgroundColor: unreadOnly ? "var(--color-accent)" : "transparent" }}
              >
                {unreadOnly && <span className="text-white text-[8px] font-bold">✓</span>}
              </span>
              Unread only
            </button>
          </div>
        </div>

        {/* Scan button */}
        <button
          onClick={handleScan}
          disabled={scanning}
          className="w-full flex items-center justify-center gap-2 rounded-xl py-3 text-sm font-semibold transition-opacity disabled:opacity-60"
          style={{ backgroundColor: "var(--color-accent)", color: "#fff" }}
        >
          {scanning
            ? <><Loader2 size={15} className="animate-spin" /> Scanning inbox…</>
            : <><ScanLine size={15} /> Scan Inbox</>
          }
        </button>

        {/* Quota note */}
        <p className="text-[10px] text-center" style={{ color: "var(--color-text-tertiary)" }}>
          Scanning 50 emails uses ~255 Gmail API quota units (limit: 250/sec). Large scans may take a few seconds.
        </p>
      </div>

      {/* Error */}
      {error && (
        <div
          className="flex items-start gap-2 rounded-xl p-4 text-sm"
          style={{ backgroundColor: "var(--color-risk-high-soft)", color: "var(--color-risk-high)" }}
        >
          <AlertTriangle size={15} className="mt-0.5 shrink-0" />
          {error}
        </div>
      )}

      {/* Results */}
      {scanResult && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          <SummaryBar
            total={scanResult.total}
            high={scanResult.high_risk}
            medium={scanResult.medium_risk}
            low={scanResult.low_risk}
          />

          {scanResult.total === 0 ? (
            <div className="rounded-2xl border p-8 text-center" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
              <p className="text-sm" style={{ color: "var(--color-text-secondary)" }}>
                No emails found in the selected time range.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>
                {scanResult.total} emails analyzed — sorted by risk score. Results also appear in your Dashboard.
              </p>
              {scanResult.results.map((r) => (
                <ResultRow key={r.id} result={r} />
              ))}
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
