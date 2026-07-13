/**
 * PsychShield API client
 * --------------------------------------------------------------
 * Single point of contact between the React frontend and the
 * FastAPI backend. Centralizing requests here means:
 *   - one place to change the base URL (e.g. for deployment)
 *   - one place to attach auth headers once auth exists
 *   - consistent error handling and response shape across the app
 *
 * Backend routes this expects (per System Architecture diagram):
 *   POST /api/analyze-email      -> runs the 4-module pipeline
 *   POST /api/analyze-emails     -> splits one document into multiple emails server-side
 *   GET  /api/emails             -> list analyzed emails (Dashboard)
 *   GET  /api/emails/:id         -> single AnalysisResult (Analysis Interface)
 *   GET  /api/analytics          -> aggregate stats (Admin Panel)
 *   GET  /api/audit-log          -> AuditLog records (Admin Panel)
 * --------------------------------------------------------------
 */

let _authToken = null;
export function setAuthToken(token) { _authToken = token; }

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(message, status, payload) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(_authToken ? { "Authorization": `Bearer ${_authToken}` } : {}),
      ...options.headers,
    },
    ...options,
  });

  let body = null;
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    body = await res.json().catch(() => null);
  }

  if (!res.ok) {
    throw new ApiError(body?.detail || res.statusText || "Request failed", res.status, body);
  }

  return body;
}

export const api = {
  /** Register a new user account */
  register: (payload) =>
    request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  /** Authenticate an existing user */
  login: (payload) =>
    request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  /** Authenticate via Google OAuth */
  googleAuth: (credential) =>
    request("/api/auth/google", {
      method: "POST",
      body: JSON.stringify({ credential }),
    }),

  analyzeEmail: (payload) =>
    request("/api/analyze-email", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  /** Submit one document containing multiple emails; the backend splits and
   * analyzes each as a separate entity — used by any client that doesn't
   * want to pre-split client-side (this UI still does its own splitting
   * for instant per-chunk progress feedback; see EmailAnalysis.jsx). */
  analyzeEmails: (document) =>
    request("/api/analyze-emails", {
      method: "POST",
      body: JSON.stringify({ document }),
    }),

  /** Fetch paginated list of previously analyzed emails for the Dashboard */
  getEmails: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/api/emails${query ? `?${query}` : ""}`);
  },

  /** Fetch one email's full AnalysisResult (emotion, manipulation, link, risk) */
  getEmailById: (id) => request(`/api/emails/${id}`),

  /** Fetch aggregate analytics for the Admin Panel */
  getAnalytics: () => request("/api/analytics"),

  /** Fetch the AuditLog for the Admin Panel */
  getAuditLog: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/api/audit-log${query ? `?${query}` : ""}`);
  },

  /** Request a password reset email */
  forgotPassword: (payload) =>
    request("/api/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  /** Complete password reset with token */
  resetPassword: (payload) =>
    request("/api/auth/reset-password", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  /** Check if a reset token is still valid */
  validateResetToken: (token) =>
    request("/api/auth/validate-reset-token", {
      method: "POST",
      body: JSON.stringify({ token }),
    }),

  /** Gmail integration */
  gmailStatus: () => request("/api/gmail/status"),
  gmailConnect: () => request("/api/gmail/connect"),
  gmailDisconnect: () => request("/api/gmail/disconnect"),
  gmailScan: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/api/gmail/scan${query ? `?${query}` : ""}`, { method: "POST" });
  },
};

export function downloadReport(period) {
  const url = `${API_BASE_URL}/api/reports/download?period=${period}`;
  return fetch(url, {
    headers: _authToken ? { Authorization: `Bearer ${_authToken}` } : {},
  }).then((res) => {
    if (!res.ok) throw new ApiError("Download failed", res.status);
    return res.blob();
  }).then((blob) => {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `psychshield_${period}_report.csv`;
    a.click();
    URL.revokeObjectURL(a.href);
  });
}

export { ApiError, API_BASE_URL };
