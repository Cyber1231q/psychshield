const TIER_STYLES = {
  Low: { bg: "var(--color-risk-low-soft)", fg: "var(--color-risk-low)" },
  Medium: { bg: "var(--color-risk-medium-soft)", fg: "var(--color-risk-medium)" },
  High: { bg: "var(--color-risk-high-soft)", fg: "var(--color-risk-high)" },
};

export default function RiskBadge({ tier, score, size = "md" }) {
  const style = TIER_STYLES[tier] || TIER_STYLES.Low;
  const sizeClasses = size === "sm" ? "text-[11px] px-2 py-0.5 gap-1" : "text-xs px-2.5 py-1 gap-1.5";

  return (
    <span
      className={`inline-flex items-center rounded-md font-mono font-semibold tracking-wide ${sizeClasses}`}
      style={{ backgroundColor: style.bg, color: style.fg }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: style.fg }} />
      {tier.toUpperCase()}
      {typeof score === "number" && <span className="opacity-70">· {score}</span>}
    </span>
  );
}
