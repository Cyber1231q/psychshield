import { motion } from "framer-motion";
import { TRIGGER_META } from "../../lib/mockData";

const TRIGGER_COLORS = {
  urgency:   "#ef4444",
  fear:      "#a855f7",
  authority: "#3b82f6",
  trust:     "#22c55e",
  pity:      "#f59e0b",
};

const KEYS = ["urgency", "fear", "authority", "trust", "pity"];
const CX = 200;
const CY = 200;
const R = 140;
const RINGS = [25, 50, 75, 100];

function polarToXY(angleDeg, radius) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: CX + radius * Math.cos(rad), y: CY + radius * Math.sin(rad) };
}

export default function TriggerMap({ triggers, animate = true, compact = false }) {
  const angleStep = 360 / KEYS.length;

  const points = KEYS.map((key, i) => {
    const value = triggers[key] || 0;
    const angle = i * angleStep;
    const r = (value / 100) * R;
    return { key, value, angle, ...polarToXY(angle, r) };
  });

  const polygonPoints = points.map((p) => `${p.x},${p.y}`).join(" ");

  return (
    <div className="flex flex-col items-center gap-5 w-full">
      <svg
        viewBox="0 0 400 400"
        className="select-none w-full"
        style={{ maxWidth: compact ? 320 : 460 }}
      >
        <defs>
          {KEYS.map((key) => (
            <radialGradient key={`grad-${key}`} id={`grad-${key}`}>
              <stop offset="0%" stopColor={TRIGGER_COLORS[key]} stopOpacity={0.35} />
              <stop offset="100%" stopColor={TRIGGER_COLORS[key]} stopOpacity={0.05} />
            </radialGradient>
          ))}
        </defs>

        {/* Ring grid */}
        {RINGS.map((pct) => (
          <circle
            key={pct}
            cx={CX} cy={CY} r={(pct / 100) * R}
            fill="none"
            stroke="var(--color-border)"
            strokeWidth={0.6}
            opacity={0.4}
          />
        ))}

        {/* Axis lines */}
        {KEYS.map((key, i) => {
          const angle = i * angleStep;
          const tip = polarToXY(angle, R + 6);
          return (
            <line
              key={`axis-${key}`}
              x1={CX} y1={CY} x2={tip.x} y2={tip.y}
              stroke={TRIGGER_COLORS[key]}
              strokeWidth={0.8}
              opacity={0.3}
            />
          );
        })}

        {/* Colored wedge fills with gradient */}
        {KEYS.map((key, i) => {
          const value = triggers[key] || 0;
          if (value < 1) return null;
          const angle = i * angleStep;
          const halfWedge = angleStep / 2 - 1;
          const r = (value / 100) * R;
          const a1 = polarToXY(angle - halfWedge, r);
          const a2 = polarToXY(angle + halfWedge, r);
          const largeArc = halfWedge * 2 > 180 ? 1 : 0;
          const path = `M ${CX} ${CY} L ${a1.x} ${a1.y} A ${r} ${r} 0 ${largeArc} 1 ${a2.x} ${a2.y} Z`;
          return (
            <motion.path
              key={key}
              d={path}
              fill={`url(#grad-${key})`}
              initial={animate ? { opacity: 0 } : { opacity: 1 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: i * 0.1 }}
            />
          );
        })}

        {/* Data polygon — blended fill using each trigger color at its edge */}
        <motion.polygon
          points={polygonPoints}
          fill="var(--color-accent)"
          fillOpacity={0.06}
          stroke="var(--color-accent)"
          strokeWidth={2}
          strokeLinejoin="round"
          initial={animate ? { opacity: 0, scale: 0.2 } : {}}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          style={{ transformOrigin: `${CX}px ${CY}px` }}
        />

        {/* Colored edge segments on the polygon */}
        {points.map((p, i) => {
          const next = points[(i + 1) % points.length];
          return (
            <motion.line
              key={`edge-${p.key}`}
              x1={p.x} y1={p.y} x2={next.x} y2={next.y}
              stroke={TRIGGER_COLORS[p.key]}
              strokeWidth={2.5}
              strokeLinecap="round"
              opacity={0.7}
              initial={animate ? { pathLength: 0 } : {}}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.5, delay: 0.3 + i * 0.08 }}
            />
          );
        })}

        {/* Data dots */}
        {points.map((p, i) => (
          <motion.circle
            key={p.key}
            cx={p.x} cy={p.y} r={compact ? 5 : 7}
            fill={TRIGGER_COLORS[p.key]}
            stroke="var(--color-bg-elevated)"
            strokeWidth={2.5}
            initial={animate ? { opacity: 0, scale: 0 } : {}}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.5 + i * 0.08 }}
          />
        ))}

        {/* Trigger labels around the outside */}
        {KEYS.map((key, i) => {
          const angle = i * angleStep;
          const labelPos = polarToXY(angle, R + 35);
          const meta = TRIGGER_META[key];
          const value = triggers[key] || 0;
          return (
            <g key={`label-${key}`}>
              <text
                x={labelPos.x} y={labelPos.y - 7}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize={compact ? 12 : 15}
                fontFamily="monospace"
                fontWeight={800}
                fill={TRIGGER_COLORS[key]}
              >
                {(meta?.label || key).toUpperCase()}
              </text>
              <text
                x={labelPos.x} y={labelPos.y + 10}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize={compact ? 11 : 13}
                fontFamily="monospace"
                fontWeight={700}
                fill={TRIGGER_COLORS[key]}
                opacity={0.8}
              >
                {Math.round(value)}%
              </text>
            </g>
          );
        })}
      </svg>

      {/* Legend row */}
      <div className={`flex flex-wrap justify-center ${compact ? "gap-3" : "gap-4"}`}>
        {KEYS.map((key) => {
          const meta = TRIGGER_META[key];
          const value = triggers[key] || 0;
          return (
            <div key={key} className="flex items-center gap-2">
              <span
                className="inline-block rounded-full"
                style={{
                  width: compact ? 8 : 10,
                  height: compact ? 8 : 10,
                  backgroundColor: TRIGGER_COLORS[key],
                  boxShadow: `0 0 6px ${TRIGGER_COLORS[key]}60`,
                }}
              />
              <span
                className={`font-mono font-semibold ${compact ? "text-[10px]" : "text-xs"}`}
                style={{ color: "var(--color-text-secondary)" }}
              >
                {meta?.label || key} {Math.round(value)}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
