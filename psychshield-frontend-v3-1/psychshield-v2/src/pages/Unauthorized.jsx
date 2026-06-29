import { Link } from "react-router-dom";
import { ShieldX } from "lucide-react";

export default function Unauthorized() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-6 text-center">
      <ShieldX size={40} style={{ color: "var(--color-risk-high)" }} />
      <h1 className="mt-4 text-2xl font-bold" style={{ color: "var(--color-text-primary)" }}>
        Access denied
      </h1>
      <p className="mt-2 max-w-sm text-sm" style={{ color: "var(--color-text-secondary)" }}>
        Your account role does not have permission to view this page. Contact your
        system administrator if you believe this is an error.
      </p>
      <Link
        to="/dashboard"
        className="focus-ring mt-6 inline-flex items-center gap-2 rounded-lg px-5 py-3 text-sm font-semibold"
        style={{ backgroundColor: "var(--color-accent)", color: "var(--color-bg-elevated)" }}
      >
        Back to dashboard
      </Link>
    </div>
  );
}
