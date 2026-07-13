# PsychShield

**AI-Based Email Social Engineering Detection and Prediction System**

A final-year project by Olatunji David Imoelayo, Department of Cybersecurity, Caleb University, Imota Lagos (2026).

---

## The Problem

Over 90% of data breaches start with a social engineering email. These attacks don't succeed because of technical sophistication; they succeed because they exploit how people think. An email that says "your account will be suspended in 24 hours" isn't dangerous because of a bad link. It's dangerous because it creates panic, and panic makes people click without thinking.

Traditional security tools miss this entirely. They check for blacklisted URLs and malware signatures. If the email has none of those, it sails right through. But the most effective phishing emails today are psychologically crafted, no malware needed, just the right combination of urgency, fear, and fake authority.

## What PsychShield Does

PsychShield analyzes the psychology behind an email, not just the technical indicators. When you submit an email for analysis, four detection modules run:

1. **Emotion Detection.** A machine learning model (trained on over 43,000 real text samples) identifies which psychological triggers the email is using: urgency, fear, authority, trust, or pity. It combines AI predictions with keyword and phrase matching for maximum accuracy.

2. **Manipulation Pattern Recognition.** Scans for over a dozen categories of social engineering techniques, from artificial time pressure and threat of loss to more subtle tactics like confidentiality coercion (the "don't tell anyone about this" trick used in CEO fraud) and financial urgency.

3. **Link Verification.** Every URL in the email is checked against a database of known phishing URLs, tested for typosquatting (e.g., "paypa1.com" pretending to be "paypal.com"), and flagged for suspicious patterns like IP-based hostnames or sketchy domain extensions.

4. **Sender Verification.** Checks whether the sender's domain is impersonating a known brand, and whether it actually passes SPF/DKIM/DMARC. Gmail-scanned emails get a real per-message verdict straight from Google's own delivery headers. Pasted or uploaded emails get a live DNS lookup plus a domain-age check instead, since there's no delivery envelope to inspect. Where something genuinely can't be verified (DKIM for a bare sender address, for example, with no signed message bytes to check it against), it's reported as unverifiable rather than guessed at.

**Risk Scoring** combines all four signals into a single 0-100 risk score using a weighted formula that adapts to whichever signals are actually available for a given email. The email is classified as HIGH (60+), MEDIUM (40-59), or LOW (under 40), with a plain-English explanation of exactly why it scored that way.

## Connecting Gmail

Beyond pasting or uploading, PsychShield can connect directly to a Gmail inbox (read-only, `gmail.readonly` scope, so it can never send, delete, or modify anything) and scan messages through the same four-module pipeline. Every scanned message becomes its own separate, individually-scored entity. The OAuth handshake runs in a popup window rather than a full-page redirect, specifically so the app's session token, which is deliberately kept in memory only and never in localStorage, survives the round trip to Google and back.

## How Well It Works

We tested PsychShield against real phishing templates (PayPal scams, Microsoft credential harvests, Nigerian 419 fraud, CEO wire fraud, WhatsApp scams, Netflix billing scams, JAMB admission scams, and more) alongside genuine business emails from a university environment.

- **Emotion model accuracy:** 91.05%
- **Overall detection accuracy:** 100% on real-world test samples
- **False positives:** Zero. No legitimate email was incorrectly flagged.
- **False negatives:** Zero. Every phishing email was caught.
- **Speed:** Around 3ms per analysis

## Features at a Glance

- **Single or batch analysis.** Paste one email or upload a file with dozens; each becomes its own separately-scored entity, with its sender automatically extracted. Splitting happens both in the browser (instant feedback) and on the backend (`POST /analyze-emails`, using Python's real `email` module), so the same behavior works for any client, not just this app.
- **Supports .eml, .txt, .msg, .mbox, .docx, and .pdf files.** All parsed client-side, with magic-byte verification (checking real file signatures, not just the extension), size ceilings, and a zip-bomb guard on `.docx`.
- **Gmail inbox scanning.** Connect a Gmail account read-only and scan messages directly, each scored individually through the same pipeline.
- **Visual trigger map.** A radar chart shows which psychological buttons the email is pressing, with color-coded indicators for each trigger type.
- **Investigation panel.** HIGH-risk emails get a detailed breakdown: full email content, sender identity, domain verification (SPF/DKIM/DMARC, domain age), typosquatting detection, and every flagged URL with explanations.
- **Dashboard.** Track all analyzed emails with stats, a 7-day trend chart, and tier-based filtering. Download weekly, monthly, or yearly reports as CSV files.
- **Admin panel.** Model performance metrics, organization-wide trigger frequency charts, a full audit log, and user management.
- **Dark mode.** Toggle between light and dark themes. Your preference is saved automatically.

## Tech Stack

| What | Built With |
|---|---|
| Frontend | React, Vite, Tailwind CSS, Framer Motion, Recharts, pdfjs-dist |
| Backend | Python with FastAPI |
| Machine Learning | TF-IDF + LinearSVC, trained on the GoEmotions dataset |
| Database | SQLite for development (Postgres-capable), Alembic-managed migrations |
| Authentication | JWT tokens with bcrypt password hashing, Google OAuth login |
| Gmail integration | Google OAuth2, Fernet-encrypted token storage |
| Rate limiting | In-memory by default; Redis-backed automatically if `REDIS_URL` is set |

## Running the Project

You need to start two things: the backend API and the frontend app. Both read a `.env` file that isn't committed to the repo (see **Environment Setup** below), so copy the `.example` template first or nothing will start correctly.

**Start the backend:**
```bash
cd backend
cp .env.example .env        # then fill in the values, see Environment Setup
pip install -r requirements.txt
alembic upgrade head         # applies database migrations
python -m uvicorn main:app --reload --port 8000
```
This starts the API at `http://localhost:8000`. It automatically loads the phishing database and the trained ML model on startup.

**Start the frontend:**
```bash
cd psychshield-frontend-v3-1/psychshield-v2
cp .env.example .env         # then fill in VITE_GOOGLE_CLIENT_ID if using Google sign-in
npm install
npm run dev
```
This starts the app at `http://localhost:5173`. Open that URL in Chrome, Edge, or Firefox.

The frontend already knows where the backend is (`VITE_API_BASE_URL` in `.env`, defaults to `http://localhost:8000`). You don't need to change anything unless your backend runs on a different port.

## Environment Setup

Neither `.env` file is committed. Both are gitignored, and `backend/.env.example` / `psychshield-v2/.env.example` are the templates to copy from. At minimum, the backend needs a real `JWT_SECRET` (a long random string) for sessions to survive a restart. Everything else has a safe default or degrades gracefully if left unset:

| Variable | Required? | What happens if unset |
|---|---|---|
| `JWT_SECRET` | Recommended | A random one is generated at startup, so sessions won't survive a restart |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URI` | Only for Google sign-in / Gmail scanning | Those two features are simply unavailable |
| `TOKEN_ENCRYPTION_KEY` | Only if using Gmail | An ephemeral key is generated, so stored Gmail tokens won't survive a restart |
| `REDIS_URL` | No | Rate limiting falls back to an in-memory store automatically |
| `PHISHTANK_CSV_PATH` / `ENRON_DATA_PATH` | No | Link verification and model training run with reduced/no real-world data |

**Never commit a real `.env` file, a downloaded Google OAuth `client_secret_*.json`, or any API key/token to this repository.** `.gitignore` blocks the common patterns, but it can't catch a value pasted directly into a tracked file.

## Security

PsychShield was built with security in mind from the start. Here's what's in place:

- Passwords are hashed with bcrypt and must meet complexity requirements (8+ characters with uppercase, lowercase, digits, and special characters).
- Authentication uses JWT tokens that expire after 8 hours.
- Login is rate-limited. After 5 failed attempts in 5 minutes, the account is temporarily locked.
- Password reset uses secure, hashed tokens that expire in 15 minutes and can only be used once. Token comparison uses constant-time algorithms to prevent timing attacks.
- All email input is validated and capped at 50KB to prevent abuse.
- Each user can only see their own analyzed emails. There's no cross-user data leakage.
- Sensitive routes (audit log, model metrics) are restricted to admin accounts.
- Every action, including logins, failed attempts, analyses, and password resets, is recorded in an immutable audit log.
- There are no default accounts. Everyone has to register.
- The codebase was audited against the OWASP Top 10 and all identified flaws were patched.
- The frontend's session token lives in memory only, never localStorage, so it can't be exfiltrated by a stored-XSS payload reading browser storage.
- Gmail's OAuth tokens are encrypted at rest with Fernet (`TOKEN_ENCRYPTION_KEY`) before ever touching the database.
- File uploads (`.docx`/`.pdf`) are checked against their real file signature, not just their extension, with hard size ceilings and a zip-bomb guard. All of it runs client-side, since there is no backend file-upload endpoint at all (a smaller server attack surface by design).
- Sender authenticity (SPF/DKIM/DMARC) is graded, not binary: a failed check counts as real evidence, an unverifiable one counts for very little, and nothing is ever reported as "verified" without genuine evidence behind it.

## Pages

| Page | Who can access it | What it's for |
|---|---|---|
| Home | Everyone | Introduction to PsychShield and how it works |
| About | Everyone | The psychology behind social engineering attacks |
| Login | Everyone | Sign in with email and password |
| Sign Up | Everyone | Create a new analyst account |
| Forgot Password | Everyone | Request a password reset link via email |
| Reset Password | Everyone | Set a new password using the reset link |
| Analysis | Logged-in users | The main tool: paste or upload emails and see the full risk breakdown |
| Dashboard | Logged-in users | Overview of all analyzed emails, trends, stats, and report downloads |
| Settings | Logged-in users | Account and preference settings |
| Admin Panel | Admins only | Model performance, trigger analytics, audit trail, user management |

## Project Layout

```
Frontend (psychshield-v2/src/)
  components/     UI pieces: navbar, footer, risk badges, trigger map, Gmail widgets
  context/        Auth and theme state management
  lib/            API client and mock data
  pages/          All the pages listed above
  test/           Vitest setup

Backend (backend/)
  detectors/      The four detection modules (emotion, pattern, link, sender)
  routers/        API route handlers for auth, analysis (single + batch), gmail, emails, analytics, reports
  models/         Database models and request/response schemas
  integrations/   Gmail OAuth2 + inbox fetch
  data/loaders/   Dataset loaders for GoEmotions, PhishTank, and Enron
  evaluation/     Model evaluation scripts (generates the thesis Chapter 4 metrics)
  saved_models/   The trained ML model files
  utils/          Rate limiting, password-reset email sending
  alembic/        Database migrations
  tests/          All test suites
```

## Running Tests

**Backend:**
```bash
cd backend
python -m pytest tests/ -v
```

81 backend tests across unit, integration, false-positive, and real-world classification suites.

**Frontend:**
```bash
cd psychshield-frontend-v3-1/psychshield-v2
npm test
```

18 tests covering auth state, protected routing, and the Gmail connect flow.

---

Built as a final-year project for the Department of Cybersecurity, Caleb University, Imota Lagos.
