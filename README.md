# PsychShield

Most phishing tools will catch a suspicious link and quietly move 
the email to spam. Job done, no explanation given. But what about 
the emails that have no malicious link at all? The ones where 
someone is pretending to be your CEO asking for an urgent wire 
transfer, or a stranded colleague begging for gift cards?

Those emails work because they are psychologically designed to 
make you act before you think. And most security tools completely 
miss that layer.

PsychShield is my attempt to fix that. Instead of just scanning 
for technical red flags, it reads the psychology of an email, 
what emotions it is trying to trigger, what manipulation techniques 
it uses, and whether the links or sender domain look suspicious. 
Then it gives you a plain English explanation of why the email 
is dangerous, not just that it is.

I built this as my final year project in the Department of 
Cybersecurity at Caleb University, Lagos. The goal was to create 
something that could actually help security teams understand the 
threats hitting their organisation, not just block them silently.


## What it actually does

You paste an email or upload a .eml file and the system runs it 
through four detection modules at the same time:

Emotion detection — trained on 43,410 samples from Google's 
GoEmotions dataset using TF-IDF and LinearSVC. It scores five 
psychological triggers: Urgency, Fear, Authority, Trust, and Pity. 
Achieved 91.05% accuracy on the test set.

Manipulation pattern detection — twelve weighted regex categories 
covering techniques like artificial time pressure, threat of loss, 
authority impersonation, Business Email Compromise patterns, 
lottery scams, and more.

Link verification : checks every URL against 65,817 verified 
phishing URLs from PhishTank and runs structural analysis to catch 
typosquatting (detecting that paypa1.com is impersonating 
paypal.com), suspicious domains, IP based hostnames, and 
dangerous TLDs.

Risk scoring — combines all three results using a weighted formula: 
Emotion 40% plus Manipulation Patterns 35% plus Links 25%, 
producing a score from 0 to 100 with a HIGH, MEDIUM, or LOW 
classification and a written explanation.

The whole pipeline runs in about 3 milliseconds per email.


## Results

| What we measured | Result |
|---|---|
| Emotion model accuracy | 91.05% |
| Overall pipeline accuracy | 96.99% |
| False positives across 33 legitimate emails | 0 |
| False negatives across phishing variants | 0 |
| Average analysis time | ~3ms |
| Total tests passing | 122 |

It correctly catches PayPal phishing, Microsoft credential harvests, 
CEO wire fraud, WhatsApp scams, Netflix billing scams, Nigerian 
advance fee fraud, JAMB admission scams, tax refund phishing, 
and lottery scams while correctly leaving meeting reminders, 
invoices, and newsletters alone.


## Why the weights are 40/35/25

Emotion gets the highest weight because that is the point. 
Social engineering succeeds psychologically, not technically. 
A CEO fraud email that pressures someone into wiring $47,000 
often contains no malicious link at all. It just creates urgency 
and invokes authority. If you weight links highest in your formula, 
you miss that entirely.

The 40/35/25 split reflects the actual mechanism of social 
engineering attacks, not just what is easiest to measure.


## Features

Paste email text or upload .eml files for instant analysis

Bulk email upload to analyze multiple emails at once

Dashboard with a 7 day trend chart showing which psychological 
triggers are being used most against your organisation

Radar chart showing the average emotional profile across all 
analyzed emails

HIGH risk emails get a full investigation panel with complete 
email content, sender identity, SPF/DKIM/DMARC status, and 
flagged URLs preserved for incident response

Download analysis reports as CSV weekly, monthly, or yearly

Light and dark mode

Role based access with admin and analyst accounts having 
different permissions

Full audit log of every login, analysis, and password reset

Secure password reset with time limited one time tokens


## Tech stack

| Layer | What I used |
|---|---|
| Frontend | React 19, Vite, Tailwind CSS v4, Framer Motion, Recharts |
| Backend | Python FastAPI |
| ML model | scikit-learn TF-IDF and LinearSVC |
| Training data | GoEmotions dataset (Demszky et al., 2020) |
| Threat intelligence | PhishTank (65,817 verified phishing URLs) |
| Database | SQLite with SQLAlchemy |
| Auth | JWT with bcrypt password hashing |


## Running it locally

You need both the backend and frontend running at the same time.

Backend:
```bash
cd backend
pip install -r requirements.txt
python database_init.py
python -m uvicorn main:app --reload --port 8000
```

Frontend:
```bash
cd psychshield-frontend-v3-1/psychshield-v2
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

The backend API runs at http://localhost:8000. You can explore 
all the API routes at http://localhost:8000/docs.

Copy backend/.env.example to backend/.env. The defaults work 
for local development.

Two accounts are created automatically on first startup:

Admin: admin@calebuniversity.edu.ng / admin123
Analyst: analyst@calebuniversity.edu.ng / analyst123

Change these before deploying to any real environment.


## Security

A few things I paid particular attention to since this is a 
cybersecurity project and it would be embarrassing to ship 
something with basic vulnerabilities:

Passwords hashed with bcrypt, never stored as plaintext

JWT tokens with 8 hour expiry

Login rate limiting at 5 attempts per 5 minutes before lockout

Password reset tokens are SHA-256 hashed before storage, 
expire after 15 minutes, and can only be used once

Token comparison uses hmac.compare_digest to prevent timing attacks

Input validation and 50KB body size limit on all endpoints

Analysts can only see their own analyzed emails

CORS restricted to the frontend origin

Everything is logged to the audit trail


## Limitations

The emotion model only works well on English text. Social 
engineering in Yoruba, Pidgin, or French would need additional 
training data.

The PhishTank database is a static snapshot loaded at startup. 
New phishing domains are registered every day, so real time API 
integration would improve detection of very recent threats.

The system analyzes email content but does not connect to mail 
servers to verify SPF/DKIM/DMARC in real time. It reports what 
is in the headers of the email file itself.





## Author

Olatunji David Imoleayo
www.linkedin.com/in/david-olatunji123
