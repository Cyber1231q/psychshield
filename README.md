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

You paste an email, upload a file, or connect a Gmail inbox, and the 
system runs it through four detection modules at the same time:

Emotion detection: trained on 43,410 samples from Google's 
GoEmotions dataset using TF-IDF and LinearSVC. It scores five 
psychological triggers: Urgency, Fear, Authority, Trust, and Pity. 
Achieved 91.05% accuracy on the test set.

Manipulation pattern detection: weighted regex categories covering 
techniques like artificial time pressure, threat of loss, authority 
impersonation, Business Email Compromise patterns, lottery scams, 
and more.

Link verification: checks every URL against verified phishing URLs 
from PhishTank and runs structural analysis to catch typosquatting 
(detecting that paypa1.com is impersonating paypal.com), suspicious 
domains, IP based hostnames, and dangerous TLDs.

Sender verification: checks whether the sender's domain is 
impersonating a known brand, and grades SPF, DKIM, and DMARC 
against real evidence rather than guessing. A Gmail scan reads 
Google's own delivery verdict straight from the message headers, 
while a pasted or uploaded email gets a live DNS lookup plus a 
WHOIS domain-age check instead, since there's no delivery envelope 
to read. Where something genuinely can't be verified (DKIM needs 
the message's raw signed bytes, which a bare sender address 
doesn't have), it's reported as unverifiable rather than faked.

Risk scoring: combines all four signals into a score from 0 to 
100 with a HIGH, MEDIUM, or LOW classification and a written 
explanation. The weights adapt to whichever signals are actually 
available for a given email, so a plain paste with no sender still 
uses its full scoring budget across the other three instead of 
being silently capped.

The whole pipeline runs in a few milliseconds per email for the 
non-network signals; the sender stage's DNS/WHOIS lookups are 
each capped at a hard 3 second timeout and always degrade to 
"unverifiable" rather than blocking or failing the analysis.


## Results

| What we measured | Result |
|---|---|
| Emotion model accuracy | 91.05% |
| False positives across legitimate email fixtures | 0 |
| False negatives across phishing variant fixtures | 0 |
| Backend tests passing | 80 / 81 (1 pre-existing failure, unrelated to detection logic) |
| Frontend tests passing | 18 / 18 |

The emotion model accuracy above is unchanged from the original 
GoEmotions-trained model. The end-to-end pipeline accuracy figure 
I previously reported (96.99%) was measured against an earlier 
version of the risk-scoring formula and hasn't been re-measured 
since, because the weights changed and a fourth signal (Sender) 
was added, so I'd rather not restate a number I can't currently 
stand behind. Re-running `evaluation/evaluate_model.py` against 
the current formula (once the PhishTank/Enron datasets are 
populated locally, see Limitations) is on my list before citing 
a new figure.

It correctly catches PayPal phishing, Microsoft credential harvests, 
CEO wire fraud, WhatsApp scams, Netflix billing scams, Nigerian 
advance fee fraud, JAMB admission scams, tax refund phishing, 
and lottery scams while correctly leaving meeting reminders, 
invoices, and newsletters alone.


## Why the weights are 35/30/20/15

Emotion still gets the highest weight because that is the point. 
Social engineering succeeds psychologically, not technically. 
A CEO fraud email that pressures someone into wiring $47,000 
often contains no malicious link at all. It just creates urgency 
and invokes authority. If you weight links highest in your formula, 
you miss that entirely.

The fourth signal, Sender, checks whether the sender's domain is 
impersonating a known brand and whether it actually passes SPF, 
DKIM, and DMARC. It's deliberately the smallest weight (15%) 
because it's supporting evidence, not the main signal, and when 
no sender address is available at all (a plain paste with no 
"From:" line), that 15% doesn't just get lost: the other three 
weights renormalize to fill the full 100%, so a content-only 
analysis is never silently penalized for missing data it was never 
given in the first place.


## Features

Paste email text, upload a file (.eml, .txt, .msg, .mbox, .docx, .pdf), 
or connect a Gmail inbox (read-only) for instant analysis

Bulk email analysis: one document containing several emails gets 
split into separate sender+content entities and scored individually, 
either in the browser or through a dedicated batch API endpoint

Dashboard with a 7 day trend chart showing which psychological 
triggers are being used most against your organisation

Radar chart showing the average emotional profile across all 
analyzed emails

HIGH risk emails get a full investigation panel with complete 
email content, sender identity, SPF/DKIM/DMARC status, domain 
age, and flagged URLs preserved for incident response

Download analysis reports as CSV weekly, monthly, or yearly

Light and dark mode

Role based access with admin and analyst accounts having 
different permissions

Full audit log of every login, analysis, and password reset

Secure password reset with time limited one time tokens


## Tech stack

| Layer | What I used |
|---|---|
| Frontend | React 19, Vite, Tailwind CSS v4, Framer Motion, Recharts, pdfjs-dist |
| Backend | Python FastAPI |
| ML model | scikit-learn TF-IDF and LinearSVC |
| Training data | GoEmotions dataset (Demszky et al., 2020) |
| Threat intelligence | PhishTank |
| Sender verification | dnspython (SPF/DMARC), python-whois (domain age), Google Gmail API |
| Database | SQLite with SQLAlchemy, Alembic migrations |
| Auth | JWT with bcrypt password hashing, Google OAuth login |
| Rate limiting | In-memory by default, Redis-backed if configured |
| Testing | pytest (backend), Vitest + React Testing Library (frontend) |


## Running it locally

You need both the backend and frontend running at the same time.

Backend:
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
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

Copy backend/.env.example to backend/.env, and 
psychshield-frontend-v3-1/psychshield-v2/.env.example to .env in 
that same folder. The defaults work for local development; you 
only need to fill in real values for the fields you're actually 
using (Google OAuth, SMTP, Redis).

There are no default accounts. Everyone registers their own.


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

Session tokens live in memory on the frontend only, never in 
localStorage, so a stored-XSS payload can't read them out of 
browser storage

Gmail OAuth tokens are encrypted at rest (Fernet) before they 
ever touch the database

File uploads are checked against their real file signature, not 
just their extension, with size limits and a zip-bomb guard

Sender authenticity is graded honestly: a failed SPF/DKIM/DMARC 
check counts as real evidence, a check that couldn't be run 
counts for very little, and nothing is ever reported as verified 
without genuine evidence behind it


## Limitations

The emotion model only works well on English text. Social 
engineering in Yoruba, Pidgin, or French would need additional 
training data.

The PhishTank database is a static snapshot loaded at startup. 
New phishing domains are registered every day, so real time API 
integration would improve detection of very recent threats.

DKIM can only be verified for Gmail-scanned emails, where a live 
API fetch gives a real per-message verdict straight from Google. 
For a pasted or uploaded email there's no way to safely verify it: 
the raw signed message bytes a DKIM check needs simply don't 
exist for a bare sender address, and trusting a claimed header in 
arbitrary uploaded text would be trivially spoofable. It's 
reported as unverifiable rather than faked.

There's no file-upload endpoint on the backend, by design. All 
parsing happens client-side, which keeps the server's attack 
surface small at the cost of that logic only running in a browser.

The trained ML model files and the PhishTank/Enron datasets aren't 
in this repo (too large for GitHub). A fresh clone runs the 
emotion detector in keyword-fallback mode and the link verifier 
with no PhishTank data until `train_emotion_model.py` is run and 
the datasets are populated locally.





## Author

Olatunji David Imoleayo
www.linkedin.com/in/david-olatunji123
