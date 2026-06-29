/**
 * Login Page
 * ----------------------------------------------------------
 * Authenticates users before granting access to protected routes.
 * After login, redirects to the page they originally tried to visit,
 * or /dashboard by default.
 * ----------------------------------------------------------
 */

import { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ShieldHalf, Mail, Lock, Loader2, AlertCircle, Eye, EyeOff } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import ThemeToggle from "../components/ui/ThemeToggle";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

export default function Login() {
  const { login, loginWithGoogle, isLoading, authError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const googleBtnRef = useRef(null);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState("");

  const from = location.state?.from?.pathname || "/dashboard";

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID || !googleBtnRef.current) return;
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.onload = () => {
      window.google?.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: async (response) => {
          const { success } = await loginWithGoogle(response.credential);
          if (success) navigate(from, { replace: true });
        },
      });
      window.google?.accounts.id.renderButton(googleBtnRef.current, {
        theme: "outline", size: "large", width: "100%", text: "signin_with",
      });
    };
    document.head.appendChild(script);
    return () => { try { document.head.removeChild(script); } catch {} };
  }, [from, loginWithGoogle, navigate]);

  async function handleSubmit(e) {
    e.preventDefault();
    setLocalError("");

    if (!email.trim()) return setLocalError("Email is required.");
    if (!password) return setLocalError("Password is required.");

    const { success, error } = await login(email.trim(), password);
    if (success) {
      navigate(from, { replace: true });
    } else {
      setLocalError(error || "Login failed. Please try again.");
    }
  }

  const errorMessage = localError || authError;

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{ backgroundColor: "var(--color-bg)" }}
    >
      {/* Minimal top bar with logo + theme toggle */}
      <div className="flex items-center justify-between px-6 py-4 border-b" style={{ backgroundColor: "var(--color-bg-elevated)" }}>
        <div className="flex items-center gap-2">
          <ShieldHalf size={20} strokeWidth={2.25} style={{ color: "var(--color-accent)" }} />
          <span className="font-mono text-[15px] font-semibold" style={{ color: "var(--color-text-primary)" }}>
            PsychShield
          </span>
        </div>
        <ThemeToggle />
      </div>

      {/* Login card */}
      <div className="flex flex-1 items-center justify-center px-4 py-16">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-md"
        >
          {/* Header */}
          <div className="mb-8 text-center">
            <div
              className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl border"
              style={{ backgroundColor: "var(--color-accent-soft)", borderColor: "var(--color-border-strong)" }}
            >
              <ShieldHalf size={26} strokeWidth={2} style={{ color: "var(--color-accent)" }} />
            </div>
            <h1 className="text-2xl font-bold tracking-tight" style={{ color: "var(--color-text-primary)" }}>
              Sign in to PsychShield
            </h1>
            <p className="mt-2 text-sm" style={{ color: "var(--color-text-secondary)" }}>
              Secure access for authorised security personnel only
            </p>
          </div>

          {/* Form card */}
          <div
            className="rounded-2xl border p-8"
            style={{ backgroundColor: "var(--color-bg-elevated)", boxShadow: "var(--shadow-card)" }}
          >
            <form onSubmit={handleSubmit} noValidate>
              {/* Error banner */}
              {errorMessage && (
                <motion.div
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mb-5 flex items-start gap-2.5 rounded-lg p-3 text-sm"
                  style={{ backgroundColor: "var(--color-risk-high-soft)", color: "var(--color-risk-high)" }}
                >
                  <AlertCircle size={15} className="mt-0.5 shrink-0" />
                  {errorMessage}
                </motion.div>
              )}

              {/* Email field */}
              <div className="mb-4">
                <label
                  htmlFor="email"
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
                    id="email"
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

              {/* Password field */}
              <div className="mb-6">
                <label
                  htmlFor="password"
                  className="mb-1.5 block text-sm font-medium"
                  style={{ color: "var(--color-text-primary)" }}
                >
                  Password
                </label>
                <div className="relative">
                  <Lock
                    size={15}
                    className="absolute left-3.5 top-1/2 -translate-y-1/2"
                    style={{ color: "var(--color-text-tertiary)" }}
                  />
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="focus-ring w-full rounded-lg border py-3 pl-10 pr-12 text-sm"
                    style={{
                      backgroundColor: "var(--color-bg-sunken)",
                      borderColor: "var(--color-border)",
                      color: "var(--color-text-primary)",
                    }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 focus-ring rounded"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword
                      ? <EyeOff size={15} style={{ color: "var(--color-text-tertiary)" }} />
                      : <Eye size={15} style={{ color: "var(--color-text-tertiary)" }} />
                    }
                  </button>
                </div>
              </div>

              <div className="mb-6 flex justify-end">
                <Link
                  to="/forgot-password"
                  className="text-xs font-medium focus-ring rounded"
                  style={{ color: "var(--color-accent)" }}
                >
                  Forgot password?
                </Link>
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={isLoading}
                className="focus-ring inline-flex w-full items-center justify-center gap-2 rounded-lg py-3 text-sm font-semibold transition-opacity disabled:opacity-60"
                style={{ backgroundColor: "var(--color-accent)", color: "var(--color-bg-elevated)" }}
              >
                {isLoading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Signing in...
                  </>
                ) : (
                  "Sign in"
                )}
              </button>
            </form>

            {GOOGLE_CLIENT_ID && (
              <>
                <div className="my-5 flex items-center gap-3">
                  <div className="flex-1 h-px" style={{ backgroundColor: "var(--color-border)" }} />
                  <span className="text-xs font-mono" style={{ color: "var(--color-text-tertiary)" }}>or</span>
                  <div className="flex-1 h-px" style={{ backgroundColor: "var(--color-border)" }} />
                </div>
                <div ref={googleBtnRef} className="flex justify-center" />
              </>
            )}

          </div>

          <p className="mt-6 text-center text-xs" style={{ color: "var(--color-text-tertiary)" }}>
            PsychShield · Caleb University Cybersecurity Research
          </p>
          <p className="mt-3 text-center text-sm" style={{ color: "var(--color-text-secondary)" }}>
            Don't have an account?{" "}
            <Link
              to="/signup"
              className="font-semibold focus-ring rounded"
              style={{ color: "var(--color-accent)" }}
            >
              Create one
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
