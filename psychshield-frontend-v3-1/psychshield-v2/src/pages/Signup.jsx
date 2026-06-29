/**
 * Signup Page
 * ----------------------------------------------------------
 * Allows new users to create a PsychShield account.
 * Self-registered users receive the "analyst" role by default.
 * Admins can promote them to admin via the Admin Panel.
 *
 * Validation:
 *   - All fields required
 *   - Valid email format
 *   - Password >= 8 characters, contains letter + number
 *   - Passwords must match
 *
 * Real integration: swap mockRegister() for api.register() in AuthContext
 * ----------------------------------------------------------
 */

import { useState, useEffect, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ShieldHalf, Mail, Lock, User, Loader2,
  AlertCircle, Eye, EyeOff, CheckCircle2, XCircle,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import ThemeToggle from "../components/ui/ThemeToggle";

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || "";

/** Password strength rules — must match backend _PASSWORD_RULES */
const RULES = [
  { id: "length",    label: "At least 8 characters",            test: (p) => p.length >= 8 },
  { id: "uppercase", label: "Contains an uppercase letter",     test: (p) => /[A-Z]/.test(p) },
  { id: "lowercase", label: "Contains a lowercase letter",      test: (p) => /[a-z]/.test(p) },
  { id: "number",    label: "Contains a number",                test: (p) => /\d/.test(p) },
  { id: "special",   label: "Contains a special character",     test: (p) => /[!@#$%^&*()_+\-=\[\]{}|;:'",.<>?/\\`~]/.test(p) },
];

function PasswordRule({ label, passed }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      {passed
        ? <CheckCircle2 size={13} style={{ color: "var(--color-risk-low)" }} />
        : <XCircle size={13} style={{ color: "var(--color-text-tertiary)" }} />
      }
      <span style={{ color: passed ? "var(--color-risk-low)" : "var(--color-text-tertiary)" }}>
        {label}
      </span>
    </div>
  );
}

function InputField({ id, label, type, value, onChange, placeholder, autoComplete, icon: Icon, rightSlot }) {
  return (
    <div className="mb-4">
      <label
        htmlFor={id}
        className="mb-1.5 block text-sm font-medium"
        style={{ color: "var(--color-text-primary)" }}
      >
        {label}
      </label>
      <div className="relative">
        <Icon
          size={15}
          className="absolute left-3.5 top-1/2 -translate-y-1/2"
          style={{ color: "var(--color-text-tertiary)" }}
        />
        <input
          id={id}
          type={type}
          autoComplete={autoComplete}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className="focus-ring w-full rounded-lg border py-3 pl-10 pr-12 text-sm"
          style={{
            backgroundColor: "var(--color-bg-sunken)",
            borderColor: "var(--color-border)",
            color: "var(--color-text-primary)",
          }}
        />
        {rightSlot && (
          <div className="absolute right-3.5 top-1/2 -translate-y-1/2">
            {rightSlot}
          </div>
        )}
      </div>
    </div>
  );
}

export default function Signup() {
  const { register, loginWithGoogle, isLoading } = useAuth();
  const navigate = useNavigate();
  const googleBtnRef = useRef(null);

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
          if (success) navigate("/dashboard", { replace: true });
        },
      });
      window.google?.accounts.id.renderButton(googleBtnRef.current, {
        theme: "outline", size: "large", width: "100%", text: "signup_with",
      });
    };
    document.head.appendChild(script);
    return () => { try { document.head.removeChild(script); } catch {} };
  }, [loginWithGoogle, navigate]);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState("");
  const [showRules, setShowRules] = useState(false);

  const rulePassed = RULES.map((r) => ({ ...r, passed: r.test(password) }));
  const allRulesPassed = rulePassed.every((r) => r.passed);

  function validate() {
    if (!name.trim()) return "Full name is required.";
    if (!email.trim()) return "Email address is required.";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "Please enter a valid email address.";
    if (!password) return "Password is required.";
    if (!allRulesPassed) return "Password does not meet the requirements below.";
    if (password !== confirmPassword) return "Passwords do not match.";
    return null;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    const validationError = validate();
    if (validationError) return setError(validationError);

    const { success, error: regError } = await register({
      name: name.trim(),
      email: email.trim().toLowerCase(),
      password,
    });

    if (success) {
      navigate("/dashboard", { replace: true });
    } else {
      setError(regError || "Registration failed. Please try again.");
    }
  }

  const eyeButton = (show, setShow) => (
    <button
      type="button"
      onClick={() => setShow((v) => !v)}
      className="focus-ring rounded"
      aria-label={show ? "Hide password" : "Show password"}
    >
      {show
        ? <EyeOff size={15} style={{ color: "var(--color-text-tertiary)" }} />
        : <Eye size={15} style={{ color: "var(--color-text-tertiary)" }} />
      }
    </button>
  );

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--color-bg)" }}>

      {/* Top bar */}
      <div
        className="flex items-center justify-between px-6 py-4 border-b"
        style={{ backgroundColor: "var(--color-bg-elevated)" }}
      >
        <div className="flex items-center gap-2">
          <ShieldHalf size={20} strokeWidth={2.25} style={{ color: "var(--color-accent)" }} />
          <span className="font-mono text-[15px] font-semibold" style={{ color: "var(--color-text-primary)" }}>
            PsychShield
          </span>
        </div>
        <ThemeToggle />
      </div>

      {/* Signup card */}
      <div className="flex flex-1 items-center justify-center px-4 py-12">
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
              Create your account
            </h1>
            <p className="mt-2 text-sm" style={{ color: "var(--color-text-secondary)" }}>
              Join PsychShield as a security analyst
            </p>
          </div>

          {/* Form card */}
          <div
            className="rounded-2xl border p-8"
            style={{ backgroundColor: "var(--color-bg-elevated)", boxShadow: "var(--shadow-card)" }}
          >
            <form onSubmit={handleSubmit} noValidate>

              {/* Error banner */}
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

              {/* Full name */}
              <InputField
                id="name"
                label="Full name"
                type="text"
                autoComplete="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Amaka Okafor"
                icon={User}
              />

              {/* Email */}
              <InputField
                id="email"
                label="Email address"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@calebuniversity.edu.ng"
                icon={Mail}
              />

              {/* Password */}
              <InputField
                id="password"
                label="Password"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                value={password}
                onChange={(e) => { setPassword(e.target.value); setShowRules(true); }}
                placeholder="Create a strong password"
                icon={Lock}
                rightSlot={eyeButton(showPassword, setShowPassword)}
              />

              {/* Password strength rules */}
              {showRules && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="mb-4 space-y-1.5 rounded-lg p-3"
                  style={{ backgroundColor: "var(--color-bg-sunken)" }}
                >
                  {rulePassed.map((r) => (
                    <PasswordRule key={r.id} label={r.label} passed={r.passed} />
                  ))}
                </motion.div>
              )}

              {/* Confirm password */}
              <div className="mb-6">
                <InputField
                  id="confirmPassword"
                  label="Confirm password"
                  type={showConfirm ? "text" : "password"}
                  autoComplete="new-password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Repeat your password"
                  icon={Lock}
                  rightSlot={eyeButton(showConfirm, setShowConfirm)}
                />
                {/* Match indicator */}
                {confirmPassword && (
                  <p
                    className="mt-1.5 flex items-center gap-1.5 text-xs"
                    style={{
                      color: password === confirmPassword
                        ? "var(--color-risk-low)"
                        : "var(--color-risk-high)",
                    }}
                  >
                    {password === confirmPassword
                      ? <><CheckCircle2 size={12} /> Passwords match</>
                      : <><XCircle size={12} /> Passwords do not match</>
                    }
                  </p>
                )}
              </div>

              {/* Role notice */}
              <div
                className="mb-5 rounded-lg p-3 text-xs"
                style={{ backgroundColor: "var(--color-accent-soft)", color: "var(--color-accent)" }}
              >
                New accounts are created with the <strong>Analyst</strong> role.
                A system administrator can grant Admin access from the Admin Panel.
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
                    Creating account...
                  </>
                ) : (
                  "Create account"
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

          {/* Back to login */}
          <p className="mt-6 text-center text-sm" style={{ color: "var(--color-text-secondary)" }}>
            Already have an account?{" "}
            <Link
              to="/login"
              className="font-semibold focus-ring rounded"
              style={{ color: "var(--color-accent)" }}
            >
              Sign in
            </Link>
          </p>

          <p className="mt-3 text-center text-xs" style={{ color: "var(--color-text-tertiary)" }}>
            PsychShield · Caleb University Cybersecurity Research
          </p>
        </motion.div>
      </div>
    </div>
  );
}
