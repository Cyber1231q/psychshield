import { useState, useEffect } from "react";
import { Mail, Link2Off, Loader2, ShieldCheck, AlertTriangle } from "lucide-react";
import { api, API_BASE_URL } from "../../lib/api";

// The OAuth callback page is served directly by the backend
// (http://localhost:8000/api/gmail/callback), not by this frontend origin
// (http://localhost:5173) — so the postMessage it sends arrives with
// event.origin === the backend's origin, not window.location.origin.
const BACKEND_ORIGIN = new URL(API_BASE_URL).origin;

/**
 * GmailConnect
 * ------------
 * Shows the current Gmail connection status for the logged-in user
 * and lets them connect or disconnect their inbox.
 *
 * Connect flow — runs in a POPUP, not a full-page redirect:
 *   1. Call GET /api/gmail/connect  →  receive {auth_url}
 *   2. Open auth_url in a popup window  →  Google consent screen
 *   3. Google redirects the popup to /api/gmail/callback  →  backend stores encrypted tokens
 *   4. Backend's callback page posts {source: "psychshield-gmail-oauth", status} to
 *      this tab via window.postMessage, then closes the popup
 *   5. This component receives that message, re-checks status, and re-renders as "connected"
 *
 * Why a popup and not window.location.href: the frontend's JWT lives in
 * memory only (see AuthContext — deliberately never persisted to
 * localStorage). A full-page navigation to Google and back would unload
 * the whole app and wipe that token, so the user would land back on
 * /analysis already logged out and get bounced to /login. A popup keeps
 * this tab (and its in-memory token) alive the entire time.
 *
 * Props:
 *   onStatusChange(connected: bool) — called whenever connection state changes
 */
export default function GmailConnect({ onStatusChange }) {
  const [status, setStatus] = useState(null); // null | "connected" | "disconnected"
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    checkStatus();
  }, []);

  useEffect(() => {
    function handleOAuthMessage(event) {
      if (event.origin !== BACKEND_ORIGIN) return;
      if (event.data?.source !== "psychshield-gmail-oauth") return;
      setActionLoading(false);
      if (event.data.status === "connected") {
        checkStatus();
      } else {
        setError("Gmail authorization failed. Please try again.");
      }
    }
    window.addEventListener("message", handleOAuthMessage);
    return () => window.removeEventListener("message", handleOAuthMessage);
  }, []);

  async function checkStatus() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.gmailStatus();
      const connected = data.connected;
      setStatus(connected ? "connected" : "disconnected");
      onStatusChange?.(connected);
    } catch {
      setStatus("disconnected");
      onStatusChange?.(false);
    } finally {
      setLoading(false);
    }
  }

  async function handleConnect() {
    setActionLoading(true);
    setError(null);
    try {
      const data = await api.gmailConnect();
      const popup = window.open(
        data.auth_url,
        "psychshield-gmail-oauth",
        "width=520,height=680"
      );
      if (!popup) {
        setError("Your browser blocked the Gmail sign-in popup. Please allow popups for this site and try again.");
        setActionLoading(false);
        return;
      }
      // If the user closes the popup without finishing (or completing it in
      // a browser that doesn't deliver postMessage before close), stop the
      // spinner instead of leaving it stuck.
      const pollClosed = setInterval(() => {
        if (popup.closed) {
          clearInterval(pollClosed);
          setActionLoading(false);
        }
      }, 500);
    } catch (err) {
      setError(err.message || "Could not start Gmail authorization.");
      setActionLoading(false);
    }
  }

  async function handleDisconnect() {
    setActionLoading(true);
    setError(null);
    try {
      await api.gmailDisconnect();
      setStatus("disconnected");
      onStatusChange?.(false);
    } catch (err) {
      setError(err.message || "Failed to disconnect Gmail.");
    } finally {
      setActionLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm" style={{ color: "var(--color-text-tertiary)" }}>
        <Loader2 size={14} className="animate-spin" />
        Checking Gmail status…
      </div>
    );
  }

  const isConnected = status === "connected";

  return (
    <div
      className="rounded-2xl border p-5 flex flex-col gap-4"
      style={{ backgroundColor: "var(--color-bg-elevated)" }}
    >
      {/* Header */}
      <div className="flex items-center gap-3">
        <div
          className="flex items-center justify-center w-9 h-9 rounded-xl"
          style={{ backgroundColor: isConnected ? "var(--color-risk-low-soft)" : "var(--color-bg-sunken)" }}
        >
          <Mail
            size={18}
            style={{ color: isConnected ? "var(--color-risk-low)" : "var(--color-text-tertiary)" }}
          />
        </div>
        <div>
          <p className="text-sm font-semibold" style={{ color: "var(--color-text-primary)" }}>
            Gmail Integration
          </p>
          <p className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>
            Read-only · gmail.readonly scope
          </p>
        </div>
        <div className="ml-auto">
          {isConnected ? (
            <span
              className="flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold"
              style={{ backgroundColor: "var(--color-risk-low-soft)", color: "var(--color-risk-low)" }}
            >
              <ShieldCheck size={12} /> Connected
            </span>
          ) : (
            <span
              className="rounded-full px-3 py-1 text-xs font-semibold"
              style={{ backgroundColor: "var(--color-bg-sunken)", color: "var(--color-text-tertiary)" }}
            >
              Not connected
            </span>
          )}
        </div>
      </div>

      {/* Description */}
      {!isConnected && (
        <p className="text-xs leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
          Connect your Gmail account to scan your inbox for social engineering emails.
          PsychShield only reads messages — it cannot send, delete, or modify anything.
          You can disconnect at any time.
        </p>
      )}

      {/* Error */}
      {error && (
        <div
          className="flex items-start gap-2 rounded-xl p-3 text-xs"
          style={{ backgroundColor: "var(--color-risk-high-soft)", color: "var(--color-risk-high)" }}
        >
          <AlertTriangle size={13} className="mt-0.5 shrink-0" />
          {error}
        </div>
      )}

      {/* Action button */}
      {isConnected ? (
        <button
          onClick={handleDisconnect}
          disabled={actionLoading}
          className="flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-opacity disabled:opacity-50"
          style={{ backgroundColor: "var(--color-bg-sunken)", color: "var(--color-text-secondary)" }}
        >
          {actionLoading ? <Loader2 size={14} className="animate-spin" /> : <Link2Off size={14} />}
          Disconnect Gmail
        </button>
      ) : (
        <button
          onClick={handleConnect}
          disabled={actionLoading}
          className="flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition-opacity disabled:opacity-50"
          style={{ backgroundColor: "var(--color-accent)", color: "#fff" }}
        >
          {actionLoading ? <Loader2 size={14} className="animate-spin" /> : <Mail size={14} />}
          Connect Gmail
        </button>
      )}
    </div>
  );
}
