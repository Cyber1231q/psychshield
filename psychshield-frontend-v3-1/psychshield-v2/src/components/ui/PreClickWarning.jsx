import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, X } from "lucide-react";
import { useState } from "react";

export default function PreClickWarning({ tier, score }) {
  const [dismissed, setDismissed] = useState(false);

  if (tier !== "High" || dismissed) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -8 }}
        transition={{ duration: 0.3 }}
        className="rounded-2xl border p-4 mb-5"
        style={{
          backgroundColor: "var(--color-risk-high-soft)",
          borderColor: "var(--color-risk-high)",
        }}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <AlertTriangle
              size={18}
              className="mt-0.5 shrink-0"
              style={{ color: "var(--color-risk-high)" }}
            />
            <div>
              <p className="text-sm font-semibold" style={{ color: "var(--color-risk-high)" }}>
                ⚠ Pre-click warning — do not interact with this email
              </p>
              <p className="mt-1 text-xs leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
                This email scored <strong>{score}/100</strong> and is classified as{" "}
                <strong>HIGH RISK</strong>. It contains psychological manipulation indicators
                and potentially malicious links. Do not click any links, download attachments,
                or reply until this email has been reviewed by your security team.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setDismissed(true)}
            className="focus-ring shrink-0 rounded p-1"
            aria-label="Dismiss warning"
          >
            <X size={14} style={{ color: "var(--color-text-tertiary)" }} />
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
