import { useState } from "react";
import { motion } from "framer-motion";
import { Save, Bell, Sliders, User } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import ThemeToggle from "../components/ui/ThemeToggle";
import { useTheme } from "../context/ThemeContext";

function Section({ icon: Icon, title, children }) {
  return (
    <div className="rounded-2xl border p-6" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
      <div className="flex items-center gap-2 mb-5 pb-4 border-b">
        <Icon size={16} style={{ color: "var(--color-accent)" }} />
        <h2 className="text-sm font-semibold" style={{ color: "var(--color-text-primary)" }}>
          {title}
        </h2>
      </div>
      {children}
    </div>
  );
}

function ThresholdSlider({ label, value, onChange, colorVar }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span style={{ color: "var(--color-text-secondary)" }}>{label} threshold</span>
        <span className="font-mono font-semibold" style={{ color: `var(${colorVar})` }}>
          {value}
        </span>
      </div>
      <input
        type="range"
        min={0}
        max={100}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 rounded-full appearance-none cursor-pointer"
        style={{ accentColor: `var(${colorVar})` }}
      />
    </div>
  );
}

export default function Settings() {
  const { currentUser } = useAuth();
  const { theme } = useTheme();

  // Risk thresholds — these will be sent to the backend when it's live
  const [highThreshold, setHighThreshold] = useState(70);
  const [mediumThreshold, setMediumThreshold] = useState(40);

  // Notification preferences
  const [notifyHigh, setNotifyHigh] = useState(true);
  const [notifyMedium, setNotifyMedium] = useState(false);
  const [emailDigest, setEmailDigest] = useState(true);

  const [saved, setSaved] = useState(false);

  function handleSave() {
    // Real integration: await api.updateSettings({ highThreshold, mediumThreshold, notifyHigh, notifyMedium, emailDigest });
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  }

  return (
    <div className="mx-auto max-w-3xl px-6 py-12">
      <div className="mb-8">
        <p className="text-xs font-mono uppercase tracking-wide" style={{ color: "var(--color-accent)" }}>
          Settings
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight" style={{ color: "var(--color-text-primary)" }}>
          System preferences
        </h1>
      </div>

      <div className="space-y-6">
        {/* Account */}
        <Section icon={User} title="Account">
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <span style={{ color: "var(--color-text-secondary)" }}>Email</span>
              <span className="font-mono" style={{ color: "var(--color-text-primary)" }}>
                {currentUser?.email}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span style={{ color: "var(--color-text-secondary)" }}>Role</span>
              <span
                className="rounded-md px-2 py-0.5 text-xs font-mono font-semibold capitalize"
                style={{ backgroundColor: "var(--color-accent-soft)", color: "var(--color-accent)" }}
              >
                {currentUser?.role}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span style={{ color: "var(--color-text-secondary)" }}>Display theme</span>
              <ThemeToggle />
            </div>
          </div>
        </Section>

        {/* Risk thresholds */}
        <Section icon={Sliders} title="Risk thresholds">
          <p className="text-xs mb-5" style={{ color: "var(--color-text-tertiary)" }}>
            Adjust the score boundaries that determine whether an email is classified as Low,
            Medium, or High risk. Changes apply to all future analyses.
          </p>
          <div className="space-y-5">
            <ThresholdSlider
              label="High risk (score ≥)"
              value={highThreshold}
              onChange={setHighThreshold}
              colorVar="--color-risk-high"
            />
            <ThresholdSlider
              label="Medium risk (score ≥)"
              value={mediumThreshold}
              onChange={setMediumThreshold}
              colorVar="--color-risk-medium"
            />
            <div
              className="rounded-lg p-3 text-xs font-mono"
              style={{ backgroundColor: "var(--color-bg-sunken)", color: "var(--color-text-tertiary)" }}
            >
              LOW &lt; {mediumThreshold} · MEDIUM {mediumThreshold}–{highThreshold - 1} · HIGH ≥ {highThreshold}
            </div>
          </div>
        </Section>

        {/* Notifications */}
        <Section icon={Bell} title="Notifications">
          <div className="space-y-4">
            {[
              { label: "Alert me on High risk emails", value: notifyHigh, onChange: setNotifyHigh },
              { label: "Alert me on Medium risk emails", value: notifyMedium, onChange: setNotifyMedium },
              { label: "Send daily digest to my email", value: emailDigest, onChange: setEmailDigest },
            ].map(({ label, value, onChange }) => (
              <div key={label} className="flex items-center justify-between">
                <span className="text-sm" style={{ color: "var(--color-text-secondary)" }}>
                  {label}
                </span>
                <button
                  type="button"
                  onClick={() => onChange(!value)}
                  aria-checked={value}
                  role="switch"
                  className="relative h-6 w-11 rounded-full border transition-colors"
                  style={{
                    backgroundColor: value ? "var(--color-accent)" : "var(--color-bg-sunken)",
                    borderColor: value ? "var(--color-accent)" : "var(--color-border-strong)",
                  }}
                >
                  <span
                    className="absolute top-0.5 h-5 w-5 rounded-full transition-transform"
                    style={{
                      backgroundColor: "var(--color-bg-elevated)",
                      transform: value ? "translateX(20px)" : "translateX(2px)",
                    }}
                  />
                </button>
              </div>
            ))}
          </div>
        </Section>

        {/* Save button */}
        <div className="flex items-center justify-end gap-3">
          {saved && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-sm"
              style={{ color: "var(--color-risk-low)" }}
            >
              Settings saved
            </motion.span>
          )}
          <button
            type="button"
            onClick={handleSave}
            className="focus-ring inline-flex items-center gap-2 rounded-lg px-5 py-3 text-sm font-semibold"
            style={{ backgroundColor: "var(--color-accent)", color: "var(--color-bg-elevated)" }}
          >
            <Save size={15} />
            Save preferences
          </button>
        </div>
      </div>
    </div>
  );
}
