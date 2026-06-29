# PsychShield

**AI-Based Email Social Engineering Detection and Prediction System**

A final-year project by Olatunji David Imoelayo, Department of Cybersecurity, Caleb University, Imota Lagos (2026).

---

## The Problem

Over 90% of data breaches start with a social engineering email. These attacks don't succeed because of technical sophistication — they succeed because they exploit how people think. An email that says "your account will be suspended in 24 hours" isn't dangerous because of a bad link. It's dangerous because it creates panic, and panic makes people click without thinking.

Traditional security tools miss this entirely. They check for blacklisted URLs and malware signatures. If the email has none of those, it sails right through. But the most effective phishing emails today are psychologically crafted — no malware needed, just the right combination of urgency, fear, and fake authority.

## What PsychShield Does

PsychShield analyzes the psychology behind an email, not just the technical indicators. When you submit an email for analysis, four detection modules run simultaneously:

1. **Emotion Detection** — A machine learning model (trained on over 43,000 real text samples) identifies which psychological triggers the email is using: urgency, fear, authority, trust, or pity. It combines AI predictions with keyword and phrase matching for maximum accuracy.

2. **Manipulation Pattern Recognition** — Scans for 12 categories of social engineering techniques, from artificial time pressure and threat of loss to more subtle tactics like confidentiality coercion (the "don't tell anyone about this" trick used in CEO fraud) and financial urgency.

3. **Link Verification** — Every URL in the email is checked against a database of 65,000+ known phishing URLs, tested for typosquatting (e.g., "paypa1.com" pretending to be "paypal.com"), and flagged for suspicious patterns like IP-based hostnames or sketchy domain extensions.

4. **Risk Scoring** — All three signals are combined into a single 0-100 risk score using a weighted formula. The email is classified as HIGH (60+), MEDIUM (40-59), or LOW (under 40), with a plain-English explanation of exactly why it scored that way.

The whole process takes about 3 milliseconds.

## How Well It Works

We tested PsychShield against real phishing templates (PayPal scams, Microsoft credential harvests, Nigerian 419 fraud, CEO wire fraud, WhatsApp scams, Netflix billing scams, JAMB admission scams, and more) alongside genuine business emails from a university environment.

- **Emotion model accuracy:** 91.05%
- **Overall detection accuracy:** 100% on real-world test samples
- **False positives:** Zero — no legitimate email was incorrectly flagged
- **False negatives:** Zero — every phishing email was caught
- **Speed:** Around 3ms per analysis

## Features at a Glance

- **Single or batch analysis** — Paste one email or upload a file with dozens. Each email gets analyzed individually with its sender automatically extracted.
- **Supports .eml, .txt, and .docx files** — Headers are parsed, senders are identified, and the content is split into clean sections.
- **Visual trigger map** — A radar chart shows which psychological buttons the email is pressing, with color-coded indicators for each trigger type.
- **Investigation panel** — HIGH-risk emails get a detailed breakdown: full email content, sender identity, domain verification (SPF/DKIM/DMARC), typosquatting detection, and every flagged URL with explanations.
- **Dashboard** — Track all analyzed emails with stats, a 7-day trend chart, and tier-based filtering. Download weekly, monthly, or yearly reports as CSV files.
- **Admin panel** — Model performance metrics, organization-wide trigger frequency charts, a full audit log, and user management.
- **Dark mode** — Toggle between light and dark themes. Your preference is saved automatically.

## Tech Stack

| What | Built With |
|---|---|
| Frontend | React, Vite, Tailwind CSS, Framer Motion, Recharts |
| Backend | Python with FastAPI |
| Machine Learning | TF-IDF + LinearSVC, trained on the GoEmotions dataset |
| Database | SQLite for development |
| Authentication | JWT tokens with bcrypt password hashing |

## Running the Project

You need to start two things: the backend API and the frontend app.

**Start the backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```
This starts the API at `http://localhost:8000`. It automatically loads the phishing database and the trained ML model on startup.

**Start the frontend:**
```bash
cd psychshield-frontend-v3-1/psychshield-v2
npm install
npm run dev
```
This starts the app at `http://localhost:5173`. Open that URL in Chrome, Edge, or Firefox.

The frontend already knows where the backend is (configured in the `.env` file). You don't need to change anything unless your backend runs on a different port.

## Security

PsychShield was built with security in mind from the start. Here's what's in place:

- Passwords are hashed with bcrypt and must meet complexity requirements (8+ characters with uppercase, lowercase, digits, and special characters).
- Authentication uses JWT tokens that expire after 8 hours.
- Login is rate-limited — after 5 failed attempts in 5 minutes, the account is temporarily locked.
- Password reset uses secure, hashed tokens that expire in 15 minutes and can only be used once. Token comparison uses constant-time algorithms to prevent timing attacks.
- All email input is validated and capped at 50KB to prevent abuse.
- Each user can only see their own analyzed emails — no cross-user data leakage.
- Sensitive routes (audit log, model metrics) are restricted to admin accounts.
- Every action — logins, failed attempts, analyses, password resets — is recorded in an immutable audit log.
- There are no default accounts. Everyone has to register.
- The codebase was audited against the OWASP Top 10 and all identified flaws were patched.

## Pages

| Page | Who can access it | What it's for |
|---|---|---|
| Home | Everyone | Introduction to PsychShield and how it works |
| About | Everyone | The psychology behind social engineering attacks |
| Login | Everyone | Sign in with email and password |
| Sign Up | Everyone | Create a new analyst account |
| Forgot Password | Everyone | Request a password reset link via email |
| Reset Password | Everyone | Set a new password using the reset link |
| Analysis | Logged-in users | The main tool — paste or upload emails and see the full risk breakdown |
| Dashboard | Logged-in users | Overview of all analyzed emails, trends, stats, and report downloads |
| Settings | Logged-in users | Account and preference settings |
| Admin Panel | Admins only | Model performance, trigger analytics, audit trail, user management |

## Project Layout

```
Frontend (psychshield-v2/src/)
  components/     UI pieces — navbar, footer, risk badges, trigger map
  context/        Auth and theme state management
  lib/            API client and mock data
  pages/          All the pages listed above

Backend (backend/)
  detectors/      The four detection modules
  routers/        API route handlers for auth, analysis, emails, analytics, reports
  models/         Database models and request/response schemas
  data/loaders/   Dataset loaders for GoEmotions, PhishTank, and Enron
  evaluation/     Model evaluation scripts (generates the thesis Chapter 4 metrics)
  saved_models/   The trained ML model files
  tests/          All test suites
```

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

There are 54 unit and integration tests, 48 false-positive tests, and 20 real-world classification tests. All passing.

---

Built as a final-year project for the Department of Cybersecurity, Caleb University, Imota Lagos.
