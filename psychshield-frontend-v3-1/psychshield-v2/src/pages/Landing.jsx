import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Brain, Link2, ScanSearch, Gauge, ArrowRight, AlertTriangle } from "lucide-react";
import TriggerMap from "../components/triggers/TriggerMap";
import RiskBadge from "../components/ui/RiskBadge";

const heroTriggers = { urgency: 91, fear: 82, authority: 64, trust: 11, pity: 4 };

const PILLARS = [
  {
    icon: Brain,
    title: "Emotion Detection",
    detail: "TF-IDF + SVM and GoEmotions identify fear, urgency, authority, trust, and pity in the language of an email — the same levers attackers pull on purpose.",
  },
  {
    icon: ScanSearch,
    title: "Manipulation Patterns",
    detail: "Regex and Naive Bayes models surface deceptive phrasing and influence techniques: false urgency, impersonated authority, fabricated scarcity.",
  },
  {
    icon: Link2,
    title: "Link Verification",
    detail: "Every URL is checked against PhishTank and the LegitPhish database, plus structural analysis for typosquatting and domain spoofing.",
  },
  {
    icon: Gauge,
    title: "Composite Risk Score",
    detail: "A weighted formula combines all three signals into one explainable score and tier — Low, Medium, or High — with the reasoning shown, not hidden.",
  },
];

const STEPS = [
  { n: "01", title: "Email arrives", detail: "Content is extracted and pre-processed before the sender ever reaches the inbox view." },
  { n: "02", title: "Parallel analysis", detail: "Emotion, manipulation, and link modules run simultaneously on the same email." },
  { n: "03", title: "Composite scoring", detail: "The three outputs are weighted into a single risk score with a written explanation." },
  { n: "04", title: "Pre-click warning", detail: "High and medium risk emails are flagged before the user can act on them." },
];

export default function Landing() {
  return (
    <div>
      {/* HERO */}
      <section className="mx-auto max-w-6xl px-6 pt-16 pb-20 sm:pt-24 sm:pb-28">
        <div className="grid gap-12 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div>
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="mb-5 inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-mono"
              style={{ borderColor: "var(--color-border-strong)", color: "var(--color-text-secondary)" }}
            >
              <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: "var(--color-accent)" }} />
              Psychology-aware email security
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.05 }}
              className="text-[2.5rem] leading-[1.08] font-bold tracking-tight sm:text-5xl"
              style={{ color: "var(--color-text-primary)" }}
            >
              Attackers don't exploit your inbox.{" "}
              <span style={{ color: "var(--color-accent)" }}>They exploit your mind.</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="mt-5 max-w-xl text-base leading-relaxed sm:text-lg"
              style={{ color: "var(--color-text-secondary)" }}
            >
              PsychShield reads emails the way a social engineer writes them — scoring urgency,
              fear, authority, trust, and pity alongside link and sender intelligence, so the
              manipulation is visible before you click.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.15 }}
              className="mt-8 flex flex-wrap items-center gap-4"
            >
              <Link
                to="/analysis"
                className="focus-ring inline-flex items-center gap-2 rounded-lg px-5 py-3 text-sm font-semibold transition-transform hover:-translate-y-0.5"
                style={{ backgroundColor: "var(--color-accent)", color: "var(--color-bg-elevated)" }}
              >
                Analyze an email
                <ArrowRight size={16} />
              </Link>
              <Link
                to="/dashboard"
                className="focus-ring inline-flex items-center gap-2 rounded-lg border px-5 py-3 text-sm font-semibold transition-colors hover:opacity-80"
                style={{ borderColor: "var(--color-border-strong)", color: "var(--color-text-primary)" }}
              >
                View dashboard
              </Link>
            </motion.div>
          </div>

          {/* Live-feeling scan card — the thesis, rendered */}
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.55, delay: 0.1 }}
            className="scan-texture rounded-2xl border p-5 shadow-lg"
            style={{ backgroundColor: "var(--color-bg-elevated)", boxShadow: "var(--shadow-card)" }}
          >
            <div className="flex items-center justify-between border-b pb-3">
              <div className="flex items-center gap-2">
                <AlertTriangle size={15} style={{ color: "var(--color-risk-high)" }} />
                <span className="font-mono text-xs font-medium" style={{ color: "var(--color-text-secondary)" }}>
                  scan_result.json
                </span>
              </div>
              <RiskBadge tier="High" score={91} size="sm" />
            </div>

            <div className="mt-4 space-y-1">
              <p className="text-sm font-semibold" style={{ color: "var(--color-text-primary)" }}>
                "URGENT: Your account will be suspended in 2 hours"
              </p>
              <p className="text-xs font-mono" style={{ color: "var(--color-text-tertiary)" }}>
                from security-alert@paypa1-support.com
              </p>
            </div>

            <div className="mt-5">
              <p className="mb-3 text-[11px] font-mono uppercase tracking-wide" style={{ color: "var(--color-text-tertiary)" }}>
                Psychological trigger map
              </p>
              <TriggerMap triggers={heroTriggers} compact />
            </div>

            <div
              className="mt-5 rounded-lg p-3 text-xs leading-relaxed"
              style={{ backgroundColor: "var(--color-risk-high-soft)", color: "var(--color-risk-high)" }}
            >
              Typosquatted domain detected. High fear and urgency language matches known
              account-suspension scare tactics.
            </div>
          </motion.div>
        </div>
      </section>

      {/* ABOUT */}
      <section className="mx-auto max-w-6xl px-6 py-16 border-t">
        <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr]">
          <div>
            <p className="text-xs font-mono uppercase tracking-wide" style={{ color: "var(--color-accent)" }}>
              About
            </p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight sm:text-3xl" style={{ color: "var(--color-text-primary)" }}>
              The human factor is the real attack surface
            </h2>
          </div>
          <p className="text-base leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
            Traditional phishing filters look for technical fingerprints — malformed headers,
            blacklisted IPs, malware signatures. But most social engineering succeeds by
            engineering a feeling first: panic, obligation, trust, or fear of missing out. This
            system is trained on emotion-labeled datasets including Enron email data and
            GoEmotions, combined with PhishTank threat intelligence, to score that psychological
            layer directly — and explain its reasoning instead of issuing a verdict.
          </p>
        </div>

        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {PILLARS.map((pillar) => (
            <div
              key={pillar.title}
              className="rounded-xl border p-5"
              style={{ backgroundColor: "var(--color-bg-elevated)" }}
            >
              <pillar.icon size={20} strokeWidth={2} style={{ color: "var(--color-accent)" }} />
              <h3 className="mt-4 text-sm font-semibold" style={{ color: "var(--color-text-primary)" }}>
                {pillar.title}
              </h3>
              <p className="mt-2 text-[13px] leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
                {pillar.detail}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="mx-auto max-w-6xl px-6 py-16 border-t">
        <p className="text-xs font-mono uppercase tracking-wide" style={{ color: "var(--color-accent)" }}>
          How it works
        </p>
        <h2 className="mt-2 mb-10 text-2xl font-bold tracking-tight sm:text-3xl" style={{ color: "var(--color-text-primary)" }}>
          From inbox to explainable verdict
        </h2>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, i) => (
            <div key={step.n} className="relative">
              <span
                className="font-mono text-3xl font-bold"
                style={{ color: "var(--color-border-strong)" }}
              >
                {step.n}
              </span>
              <h3 className="mt-3 text-sm font-semibold" style={{ color: "var(--color-text-primary)" }}>
                {step.title}
              </h3>
              <p className="mt-2 text-[13px] leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
                {step.detail}
              </p>
              {i < STEPS.length - 1 && (
                <div
                  className="hidden lg:block absolute top-3 -right-3 h-px w-6"
                  style={{ backgroundColor: "var(--color-border-strong)" }}
                />
              )}
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-6 py-16 border-t">
        <div
          className="rounded-2xl border p-10 text-center sm:p-14"
          style={{ backgroundColor: "var(--color-accent-soft)" }}
        >
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl" style={{ color: "var(--color-text-primary)" }}>
            See the psychology behind your inbox
          </h2>
          <p className="mx-auto mt-3 max-w-md text-sm" style={{ color: "var(--color-text-secondary)" }}>
            Paste an email and get a full trigger breakdown, link analysis, and explainable risk score.
          </p>
          <Link
            to="/analysis"
            className="focus-ring mt-6 inline-flex items-center gap-2 rounded-lg px-5 py-3 text-sm font-semibold"
            style={{ backgroundColor: "var(--color-accent)", color: "var(--color-bg-elevated)" }}
          >
            Try the analysis interface
            <ArrowRight size={16} />
          </Link>
        </div>
      </section>
    </div>
  );
}
