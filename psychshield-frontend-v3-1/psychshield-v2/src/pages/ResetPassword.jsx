import { useState, useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ShieldHalf, Lock, Loader2, CheckCircle2, AlertCircle, Eye, EyeOff, XCircle } from "lucide-react";
import { api } from "../lib/api";
import ThemeToggle from "../components/ui/ThemeToggle";

const RULES = [
  { id: "length", label: "At least 8 characters", test: (p) => p.length >= 8 },
  { id: "letter", label: "Contains a letter", test: (p) => /[a-zA-Z]/.test(p) },
  { id: "number", label: "Contains a number", test: (p) => /\d/.test(p) },
];

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token") || "";

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isValidating, setIsValidating] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const rulePassed = RULES.map((r) => ({ ...r, passed: r.test(password) }));
  const allRulesPassed = rulePassed.every((r) => r.passed);

  useEffect(() => {
    if (!token) {
      setIsValidating(false);
      return;
    }
    api.validateResetToken(token)
      .then(() => setTokenValid(true))
      .catch(() => setTokenValid(false))
      .finally(() => setIsValidating(false));
  }, [token]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (!allRulesPassed) return setError("Password does not meet requirements.");
    if (password !== confirmPassword) return setError("Passwords do not match.");

    setIsLoading(true);
    try {
      await api.resetPassword({ token, new_password: password });
      setSuccess(true);
    } catch (err) {
      setError(err?.payload?.detail || "Reset failed. Token may have expired.");
    } finally {
      setIsLoading(false);
    }
  }

  if (isValidating) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: "var(--color-bg)" }}>
        <Loader2 size={24} className="animate-spin" style={{ color: "var(--color-accent)" }} />
      </div>
    );
  }

  if (!token || !tokenValid) {
    return (
      <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--color-bg)" }}>
        <div className="flex items-center justify-between px-6 py-4 border-b" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
          <div className="flex items-center gap-2">
            <ShieldHalf size={20} style={{ color: "var(--color-accent)" }} />
            <span className="font-mono text-[15px] font-semibold" style={{ color: "var(--color-text-primary)" }}>PsychShield</span>
          </div>
          <ThemeToggle />
        </div>
        <div className="flex flex-1 items-center justify-center px-4">
          <div className="text-center max-w-sm">
            <XCircle size={40} className="mx-auto mb-4" style={{ color: "var(--color-risk-high)" }} />
            <h1 className="text-xl font-bold mb-2" style={{ color: "var(--color-text-primary)" }}>Invalid or expired link</h1>
            <p className="text-sm mb-6" style={{ color: "var(--color-text-secondary)" }}>
              This password reset link is invalid or has expired. Reset links are valid for 15 minutes and can only be used once.
            </p>
            <Link
              to="/forgot-password"
              className="focus-ring inline-flex items-center gap-2 rounded-lg px-5 py-3 text-sm font-semibold"
              style={{ backgroundColor: "var(--color-accent)", color: "var(--color-bg-elevated)" }}
            >
              Request a new link
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--color-bg)" }}>
      <div className="flex items-center justify-between px-6 py-4 border-b" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
        <div className="flex items-center gap-2">
          <ShieldHalf size={20} style={{ color: "var(--color-accent)" }} />
          <span className="font-mono text-[15px] font-semibold" style={{ color: "var(--color-text-primary)" }}>PsychShield</span>
        </div>
        <ThemeToggle />
      </div>

      <div className="flex flex-1 items-center justify-center px-4 py-12">
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
          <div className="mb-8 text-center">
            <h1 className="text-2xl font-bold" style={{ color: "var(--color-text-primary)" }}>Set your new password</h1>
          </div>

          <div
            className="rounded-2xl border p-8"
            style={{ backgroundColor: "var(--color-bg-elevated)", boxShadow: "var(--shadow-card)" }}
          >
            {success ? (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-4">
                <CheckCircle2 size={40} className="mx-auto mb-4" style={{ color: "var(--color-risk-low)" }} />
                <h2 className="text-lg font-semibold mb-2" style={{ color: "var(--color-text-primary)" }}>Password reset successful</h2>
                <p className="text-sm mb-6" style={{ color: "var(--color-text-secondary)" }}>
                  Your password has been updated. You can now sign in.
                </p>
                <Link
                  to="/login"
                  className="focus-ring inline-flex items-center gap-2 rounded-lg px-5 py-3 text-sm font-semibold"
                  style={{ backgroundColor: "var(--color-accent)", color: "var(--color-bg-elevated)" }}
                >
                  Sign in with new password
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

                <div className="mb-4">
                  <label className="mb-1.5 block text-sm font-medium" style={{ color: "var(--color-text-primary)" }}>
                    New password
                  </label>
                  <div className="relative">
                    <Lock size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2" style={{ color: "var(--color-text-tertiary)" }} />
                    <input
                      type={showPassword ? "text" : "password"}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Create a strong password"
                      className="focus-ring w-full rounded-lg border py-3 pl-10 pr-12 text-sm"
                      style={{ backgroundColor: "var(--color-bg-sunken)", borderColor: "var(--color-border)", color: "var(--color-text-primary)" }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((v) => !v)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 focus-ring rounded"
                    >
                      {showPassword
                        ? <EyeOff size={15} style={{ color: "var(--color-text-tertiary)" }} />
                        : <Eye size={15} style={{ color: "var(--color-text-tertiary)" }} />}
                    </button>
                  </div>
                </div>

                {password && (
                  <div className="mb-4 space-y-1.5 rounded-lg p-3" style={{ backgroundColor: "var(--color-bg-sunken)" }}>
                    {rulePassed.map((r) => (
                      <div key={r.id} className="flex items-center gap-2 text-xs">
                        {r.passed
                          ? <CheckCircle2 size={13} style={{ color: "var(--color-risk-low)" }} />
                          : <XCircle size={13} style={{ color: "var(--color-text-tertiary)" }} />}
                        <span style={{ color: r.passed ? "var(--color-risk-low)" : "var(--color-text-tertiary)" }}>{r.label}</span>
                      </div>
                    ))}
                  </div>
                )}

                <div className="mb-6">
                  <label className="mb-1.5 block text-sm font-medium" style={{ color: "var(--color-text-primary)" }}>
                    Confirm new password
                  </label>
                  <div className="relative">
                    <Lock size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2" style={{ color: "var(--color-text-tertiary)" }} />
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Repeat your new password"
                      className="focus-ring w-full rounded-lg border py-3 pl-10 pr-4 text-sm"
                      style={{ backgroundColor: "var(--color-bg-sunken)", borderColor: "var(--color-border)", color: "var(--color-text-primary)" }}
                    />
                  </div>
                  {confirmPassword && (
                    <p
                      className="mt-1.5 flex items-center gap-1.5 text-xs"
                      style={{ color: password === confirmPassword ? "var(--color-risk-low)" : "var(--color-risk-high)" }}
                    >
                      {password === confirmPassword
                        ? <><CheckCircle2 size={12} /> Passwords match</>
                        : <><XCircle size={12} /> Passwords do not match</>}
                    </p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="focus-ring inline-flex w-full items-center justify-center gap-2 rounded-lg py-3 text-sm font-semibold disabled:opacity-60"
                  style={{ backgroundColor: "var(--color-accent)", color: "var(--color-bg-elevated)" }}
                >
                  {isLoading
                    ? <><Loader2 size={16} className="animate-spin" /> Resetting...</>
                    : "Reset password"}
                </button>
              </form>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
