import { motion } from "framer-motion";
import { Brain, Database, FlaskConical, ShieldCheck } from "lucide-react";

const PSYCHOLOGY_PRINCIPLES = [
  {
    trigger: "Urgency",
    colorVar: "--color-trigger-urgency",
    description:
      "Attackers compress decision time artificially — 'Act within 2 hours or lose access.' Under time pressure, the prefrontal cortex (responsible for rational evaluation) is bypassed in favour of the amygdala's fight-or-flight response, causing impulsive action.",
  },
  {
    trigger: "Fear",
    colorVar: "--color-trigger-fear",
    description:
      "Threat of negative consequences ('Your account has been compromised') activates the brain's threat-detection system. Fear narrows attention and increases compliance with instructions that appear to offer a way out of danger.",
  },
  {
    trigger: "Authority",
    colorVar: "--color-trigger-authority",
    description:
      "Impersonating IT departments, banks, or executives leverages the deeply ingrained social tendency to comply with perceived authority figures (Cialdini, 1984). Victims are less likely to question instructions from someone in a position of power.",
  },
  {
    trigger: "Trust",
    colorVar: "--color-trigger-trust",
    description:
      "Familiar branding, shared context (referencing a real colleague's name), and professional language lower the recipient's defensive posture. Trust manipulation exploits the heuristic that familiarity implies safety.",
  },
  {
    trigger: "Pity",
    colorVar: "--color-trigger-pity",
    description:
      "Appeals to empathy ('I'm stranded abroad and need urgent help') exploit prosocial behaviour. The desire to help overrides scepticism, particularly when the appeal comes from an apparently known sender.",
  },
];

const DATASETS = [
  {
    icon: Database,
    name: "Enron Email Corpus",
    detail: "Over 500,000 real workplace emails used as a foundation for benign and manipulative email classification. Provides realistic linguistic context for training the emotion and manipulation detectors.",
  },
  {
    icon: Brain,
    name: "GoEmotions (Demszky et al., 2020)",
    detail: "A large-scale dataset of 58,000 Reddit comments labelled across 27 emotion categories. Used to fine-tune the emotion detection module's understanding of nuanced emotional language.",
  },
  {
    icon: ShieldCheck,
    name: "PhishTank URL Database",
    detail: "A community-verified blacklist of known phishing URLs. Provides the ground-truth threat intelligence layer for the link verification engine alongside structural URL analysis.",
  },
];

export default function About() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      {/* Header */}
      <div className="mb-12 max-w-3xl">
        <p className="text-xs font-mono uppercase tracking-wide" style={{ color: "var(--color-accent)" }}>
          About PsychShield
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl" style={{ color: "var(--color-text-primary)" }}>
          Why psychology, not just technology
        </h1>
        <p className="mt-4 text-base leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
          Traditional email security filters look for technical fingerprints: blacklisted
          domains, malformed headers, known malware signatures. But the majority of successful
          social engineering attacks contain no malware at all — they succeed by manufacturing
          an emotional state in the recipient that bypasses rational decision-making.
          PsychShield addresses this gap by analysing the psychological layer of email content
          directly, making the manipulation visible before the user acts on it.
        </p>
      </div>

      {/* Psychology principles */}
      <section className="mb-16 border-t pt-12">
        <h2 className="mb-8 text-xl font-bold" style={{ color: "var(--color-text-primary)" }}>
          The five psychological levers of social engineering
        </h2>
        <div className="space-y-6">
          {PSYCHOLOGY_PRINCIPLES.map((p, i) => (
            <motion.div
              key={p.trigger}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.07 }}
              className="flex gap-5 rounded-2xl border p-5"
              style={{ backgroundColor: "var(--color-bg-elevated)" }}
            >
              <div
                className="mt-1 h-3 w-3 shrink-0 rounded-full"
                style={{ backgroundColor: `var(${p.colorVar})` }}
              />
              <div>
                <h3 className="font-semibold text-sm mb-1" style={{ color: "var(--color-text-primary)" }}>
                  {p.trigger}
                </h3>
                <p className="text-sm leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
                  {p.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Datasets */}
      <section className="mb-16 border-t pt-12">
        <h2 className="mb-8 text-xl font-bold" style={{ color: "var(--color-text-primary)" }}>
          Training data and threat intelligence
        </h2>
        <div className="grid gap-5 sm:grid-cols-3">
          {DATASETS.map((d) => (
            <div
              key={d.name}
              className="rounded-2xl border p-5"
              style={{ backgroundColor: "var(--color-bg-elevated)" }}
            >
              <d.icon size={20} strokeWidth={2} style={{ color: "var(--color-accent)" }} />
              <h3 className="mt-4 text-sm font-semibold" style={{ color: "var(--color-text-primary)" }}>
                {d.name}
              </h3>
              <p className="mt-2 text-[13px] leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
                {d.detail}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Methodology */}
      <section className="border-t pt-12">
        <h2 className="mb-4 text-xl font-bold" style={{ color: "var(--color-text-primary)" }}>
          Research methodology
        </h2>
        <div className="flex items-start gap-4 rounded-2xl border p-6" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
          <FlaskConical size={20} strokeWidth={2} className="mt-0.5 shrink-0" style={{ color: "var(--color-accent)" }} />
          <div className="text-sm leading-relaxed space-y-3" style={{ color: "var(--color-text-secondary)" }}>
            <p>
              PsychShield was developed using the <strong style={{ color: "var(--color-text-primary)" }}>Design Science Research (DSR)</strong> methodology
              (Hevner et al., 2004; Peffers et al., 2007), which frames the system as an artefact
              designed to solve a real organisational problem rather than a purely theoretical model.
            </p>
            <p>
              Development followed three Agile sprints covering system design, module implementation,
              and evaluation. Performance targets are set at <strong style={{ color: "var(--color-text-primary)" }}>≥90% overall accuracy</strong> and
              <strong style={{ color: "var(--color-text-primary)" }}> ≥92% HIGH-tier recall</strong>, with analysis latency under 3 seconds.
            </p>
            <p>
              The composite risk score is computed as:{" "}
              <span className="font-mono text-xs" style={{ color: "var(--color-accent)" }}>
                Emotion × 0.40 + Pattern × 0.35 + Link × 0.25
              </span>
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
