import { useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ShieldHalf, Mail, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { api } from "../lib/api";
import ThemeToggle from "../components/ui/ThemeToggle";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (!email.trim()) return setError("Please enter your email address.");
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return setError("Please enter a valid email address.");
    }

    setIsLoading(true);
    try {
      await api.forgotPassword({ email: email.trim().toLowerCase() });
      setSent(true);
    } catch {
      setSent(true);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--color-bg)" }}>
      <div
        className="flex items-center justify-between px-6 py-4 border-b"
        style={{ backgroundColor: "var(--color-bg-elevated)" }}
      >
        <div className="flex items-center gap-2">
          <ShieldHalf size={20} strokeWidth={2.25} style={{ color: "var(--color-accent)" }} />
          <span
            className="font-mono text-[15px] font-semibold"
            style={{ color: "var(--color-text-primary)" }}
          >
            PsychShield
          </span>
        </div>
        <ThemeToggle />
      </div>

      <div className="flex flex-1 items-center justify-center px-4 py-16">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md"
        >
          <div className="mb-8 text-center">
            <div
              className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border"
              style={{ backgroundColor: "var(--color-accent-soft)", borderColor: "var(--color-border-strong)" }}
            >
              <Mail size={26} strokeWidth={2} style={{ color: "var(--color-accent)" }} />
            </div>
            <h1
              className="text-2xl font-bold tracking-tight"
              style={{ color: "var(--color-text-primary)" }}
            >
              Reset your password
            </h1>
            <p className="mt-2 text-sm" style={{ color: "var(--color-text-secondary)" }}>
              Enter your email and we will send you a reset link
            </p>
          </div>

          <div
            className="rounded-2xl border p-8"
            style={{ backgroundColor: "var(--color-bg-elevated)", boxShadow: "var(--shadow-card)" }}
          >
            {sent ? (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-4">
                <CheckCircle2 size={40} className="mx-auto mb-4" style={{ color: "var(--color-risk-low)" }} />
                <h2 className="text-lg font-semibold mb-2" style={{ color: "var(--color-text-primary)" }}>
                  Check your email
                </h2>
                <p className="text-sm mb-4" style={{ color: "var(--color-text-secondary)" }}>
                  If an account exists with <strong>{email}</strong>, you will receive a password reset link
                  shortly. The link expires in 15 minutes.
                </p>
                <p className="text-xs mb-6" style={{ color: "var(--color-text-tertiary)" }}>
                  For the thesis demo: check the backend terminal output for the reset link.
                </p>
                <Link
                  to="/login"
                  className="focus-ring inline-flex items-center gap-2 rounded-lg px-5 py-3 text-sm font-semibold"
                  style={{ backgroundColor: "var(--color-accent)", color: "var(--color-bg-elevated)" }}
                >
                  Back to sign in
                </Link>
              </motion.div>
            ) : (
              <form onSubmit={handleSubmit} noValidate>
                {error && (
                  <motion.div
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mb-5 flex items-start gap-2.5 rounded-lg p-3 text-sm"
                    style={{ backgroundColor: "var(--color-risk-high-soft)", color: "var(--color-risk-high)" }}
                  >
                    <AlertCircle size={15} className="mt-0.5 shrink-0" />
                    {error}
                  </motion.div>
                )}

                <div className="mb-6">
                  <label
                    htmlFor="reset-email"
                    className="mb-1.5 block text-sm font-medium"
                    style={{ color: "var(--color-text-primary)" }}
                  >
                    Email address
                  </label>
                  <div className="relative">
                    <Mail
                      size={15}
                      className="absolute left-3.5 top-1/2 -translate-y-1/2"
                      style={{ color: "var(--color-text-tertiary)" }}
                    />
                    <input
                      id="reset-email"
                      type="email"
                      autoComplete="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@calebuniversity.edu.ng"
                      className="focus-ring w-full rounded-lg border py-3 pl-10 pr-4 text-sm"
                      style={{
                        backgroundColor: "var(--color-bg-sunken)",
                        borderColor: "var(--color-border)",
                        color: "var(--color-text-primary)",
                      }}
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="focus-ring inline-flex w-full items-center justify-center gap-2 rounded-lg py-3 text-sm font-semibold transition-opacity disabled:opacity-60"
                  style={{ backgroundColor: "var(--color-accent)", color: "var(--color-bg-elevated)" }}
                >
                  {isLoading ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      Sending...
                    </>
                  ) : (
                    "Send reset link"
                  )}
                </button>
              </form>
            )}
          </div>

          <p className="mt-6 text-center text-sm" style={{ color: "var(--color-text-secondary)" }}>
            Remember your password?{" "}
            <Link to="/login" className="font-semibold focus-ring rounded" style={{ color: "var(--color-accent)" }}>
              Sign in
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
