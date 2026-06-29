"""Real-world email classification test.

Tests the pipeline against actual phishing email templates
sourced from public phishing archives and common attack patterns
seen in Nigerian university/corporate environments, plus real
legitimate corporate communications.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.chdir(os.path.join(os.path.dirname(__file__), ".."))

from detectors.emotion_detector import detect_emotions
from detectors.manipulation_detector import detect_patterns
from detectors.link_verifier import verify_links
from detectors.risk_scorer import score_email


def _analyze(body, sender=""):
    e = detect_emotions(body)
    m = detect_patterns(body)
    l = verify_links(body, sender)
    r = score_email(e, m, l)
    return r.finalScore, r.tier, len(m.techniques), [t.name for t in m.techniques]


# ═══════════════════════════════════════════════════════════════
# REAL PHISHING TEMPLATES (from public phishing archives)
# Expected: Medium or High
# ═══════════════════════════════════════════════════════════════

REAL_PHISHING = [
    (
        "PayPal classic",
        """Dear PayPal Customer,

We have noticed unusual sign-in activity on your PayPal account. As a precaution, we have limited your account until you verify your identity.

Please click the link below to restore full access to your account:
https://paypa1-account-verify.com/restore

If you do not verify within 24 hours, your account will be permanently suspended and all funds will be frozen.

Thank you for your cooperation.
PayPal Security Team""",
        "service@paypa1-account-verify.com",
    ),
    (
        "Microsoft 365 credential harvest",
        """Your Microsoft 365 password expires today.

You have received this notification because your organization requires you to update your password every 90 days. If you do not reset your password immediately, you will lose access to your email, OneDrive, and Teams.

Reset your password now: https://microsft-365-reset.xyz/update

This is an automated message from your IT department. Do not reply.

Microsoft Corporation""",
        "noreply@microsft-365-reset.xyz",
    ),
    (
        "Bank of America phishing",
        """SECURITY ALERT: Suspicious Transaction Detected

Dear Customer,

We detected an unauthorized transaction of $2,847.00 on your Bank of America account ending in ****4523.

If you did not authorize this transaction, you must verify your identity immediately to prevent further unauthorized access and permanent account restriction.

Verify Now: https://bankofamerica-secure.tk/verify-transaction

Bank of America Security Department
Ref: BOA-SEC-2026-7892""",
        "alerts@bankofamerica-secure.tk",
    ),
    (
        "Nigerian 419 advance fee",
        """Dear Friend,

I am Barrister Chukwu Emeka, a solicitor in Lagos, Nigeria. My late client, an oil magnate, left behind $15.5 million USD with no known next of kin. I am desperately seeking a trustworthy foreign partner to help transfer these funds.

You will receive 35% of the total sum for your assistance. This is urgent as the bank will freeze the account permanently if we do not act immediately.

Please help me by providing your full name, phone number, and bank details so we can begin the transfer process urgently.

I count on your kindness and support in this humanitarian matter.

Regards,
Barr. Chukwu Emeka""",
        "barrister.emeka@lawyer-ng.ml",
    ),
    (
        "CEO wire fraud / BEC",
        """Hi,

I need you to process an urgent wire transfer today. I'm in a meeting and cannot call right now.

Please wire $45,000 to the following account immediately:
Bank: First National
Account: 8827364510
Routing: 021000089

This is confidential - do not discuss with anyone else on the team. I'll explain when I'm out of my meeting.

Thanks,
Dr. Adeyemi
Vice Chancellor""",
        "vc.adeyemi@caleb-admin.xyz",
    ),
    (
        "WhatsApp verification scam",
        """Your WhatsApp account is about to expire. WhatsApp will terminate your account within 48 hours unless you verify immediately.

Click here to verify: https://whatsap-verify.gq/confirm

If this was not you, someone may have registered your phone number. Verify now to prevent unauthorized access to your messages.

WhatsApp Support Team""",
        "support@whatsap-verify.gq",
    ),
    (
        "Netflix billing scam",
        """We were unable to process your payment for your Netflix subscription.

Your account has been temporarily suspended due to a billing problem. To continue enjoying Netflix without interruption, please update your payment details within 24 hours.

Update Payment: https://netfliix-payment.top/billing

If we do not receive your updated payment information, your account will be permanently cancelled and all viewing history will be deleted.

Netflix Billing Support""",
        "billing@netfliix-payment.top",
    ),
    (
        "JAMB/university admission scam",
        """URGENT NOTIFICATION FROM JAMB

Dear Candidate,

Congratulations! You have been selected for a special admission consideration at a top Nigerian university. This offer is exclusive and only available to selected candidates.

To confirm your admission, you must pay a processing fee of N25,000 immediately before the deadline expires.

Pay now: https://jamb-admission-portal.ml/pay

Failure to pay within 24 hours will result in permanent loss of this admission opportunity. This is your final notice.

JAMB Admissions Board""",
        "admissions@jamb-admission-portal.ml",
    ),
    (
        "Google Drive sharing phish",
        """Someone shared a document with you on Google Drive.

The IT Security Department has shared "Q3 Salary Review - CONFIDENTIAL.pdf" with you. This document requires immediate review.

Open Document: https://g00gle-drive-share.xyz/doc/view

This link expires in 2 hours. If you do not open it, the document will be permanently removed from your shared folder.

Google Drive Notification""",
        "noreply@g00gle-drive-share.xyz",
    ),
    (
        "Tax refund phishing",
        """Federal Inland Revenue Service (FIRS) Notification

Dear Taxpayer,

After reviewing your annual tax records, we have determined that you are eligible for a tax refund of N847,500.00.

To claim your refund, you must verify your identity and banking details immediately through our secure portal:

https://firs-refund-portal.cf/claim

This refund expires in 48 hours. Failure to claim will result in the forfeiture of your refund permanently.

FIRS Tax Refund Department
Ref: FIRS/REF/2026/4421""",
        "refunds@firs-refund-portal.cf",
    ),
]


# ═══════════════════════════════════════════════════════════════
# REAL LEGITIMATE EMAILS (corporate/university style)
# Expected: Low
# ═══════════════════════════════════════════════════════════════

REAL_LEGITIMATE = [
    (
        "Actual IT maintenance notice",
        """Dear Staff,

Please be informed that the university network will undergo scheduled maintenance this Saturday from 11pm to 5am. During this period, email services, the student portal, and Wi-Fi may be intermittently unavailable.

No action is required on your part. All services will be restored automatically once maintenance is complete.

For questions, contact the ICT Help Desk at ext. 2450.

Regards,
ICT Department
Caleb University""",
        "ict@calebuniversity.edu.ng",
    ),
    (
        "Real HR policy update",
        """Good morning everyone,

Please find attached the updated Staff Leave Policy for the 2026/2027 academic session. Key changes include:

1. Annual leave increased from 20 to 25 working days
2. Maternity leave extended to 16 weeks
3. New provision for paternity leave (10 working days)

Please review the document and direct any questions to the HR office. The policy takes effect from August 1st.

Best regards,
Mrs. Folake Adewale
Director of Human Resources""",
        "hr@calebuniversity.edu.ng",
    ),
    (
        "Actual meeting minutes",
        """Dear Department Heads,

Attached are the minutes from the Faculty Board meeting held on June 20, 2026. Action items include:

- Submit curriculum review reports by July 15
- Nominate representatives for the accreditation committee by July 1
- Department budgets for next session due August 30

Please circulate to your respective teams.

Thank you,
Dr. Bola Okonkwo
Dean, Faculty of Computing""",
        "dean.computing@calebuniversity.edu.ng",
    ),
    (
        "Real conference invitation",
        """Dear Colleague,

You are invited to attend the 5th International Conference on Cybersecurity and Digital Forensics, hosted by the Department of Cybersecurity, Caleb University.

Date: September 15-17, 2026
Venue: Main Auditorium, Caleb University, Imota, Lagos
Theme: "Securing the Digital Future: AI-Driven Threat Detection"

Early bird registration closes August 1st. Visit our website for more details and paper submission guidelines.

We look forward to your participation.

Conference Organizing Committee""",
        "conference@calebuniversity.edu.ng",
    ),
    (
        "Real project status update",
        """Hi team,

Quick update on the PsychShield project:

- Backend API: 90% complete, all detection modules tested
- Frontend: Dashboard and analysis pages functional
- Evaluation: Model accuracy at 91.05%, exceeding our 90% target
- Remaining: Final integration testing and documentation

We're on track for the July 10 demo. Please push any pending commits by Friday.

Thanks,
Imole""",
        "imoled127@gmail.com",
    ),
    (
        "Actual exam timetable",
        """Dear Students,

The examination timetable for the 2025/2026 Second Semester has been released. Please check the student portal for your personalized schedule.

Important reminders:
- Bring your student ID to every exam
- Arrive 30 minutes before the start time
- No phones or electronic devices in the exam hall
- Results will be published 4 weeks after the last exam

For timetable conflicts, contact the Exams Office before July 1.

Office of the Registrar
Caleb University""",
        "registrar@calebuniversity.edu.ng",
    ),
    (
        "Real alumni newsletter",
        """Caleb University Alumni Newsletter - June 2026

Hello alumni!

This month's highlights:
- Class of 2026 graduation ceremony photos now available
- Alumni mentorship program launching in September
- Homecoming weekend scheduled for November 8-9
- Three alumni nominated for national technology awards

Stay connected and update your contact details on the alumni portal.

Warm regards,
Alumni Relations Office""",
        "alumni@calebuniversity.edu.ng",
    ),
    (
        "Actual Zoom meeting invite",
        """Hi all,

You're invited to our weekly project standup:

Topic: PsychShield Sprint Review
Time: Thursday, June 26, 2026 at 2:00 PM WAT
Duration: 30 minutes

Join Zoom Meeting:
https://zoom.us/j/98765432100

Please have your sprint updates ready. We'll review the detection accuracy improvements and plan the next sprint.

See you there!""",
        "lead@calebuniversity.edu.ng",
    ),
    (
        "Actual bank statement notification",
        """Dear Customer,

Your monthly account statement for June 2026 is now available. You can view and download it by logging into your GTBank internet banking account.

Account: ****7834
Statement Period: June 1 - June 30, 2026

For any discrepancies, please visit your nearest branch or call our customer service line at 0700-GTConnect.

Thank you for banking with us.
Guaranty Trust Bank""",
        "statements@gtbank.com",
    ),
    (
        "Real scholarship notification",
        """Dear Student,

We are pleased to inform you that applications for the Caleb University Merit Scholarship for the 2026/2027 session are now open.

Eligibility:
- Minimum CGPA of 4.0
- Good conduct record
- Active participation in university activities

Application deadline: August 15, 2026
Submit your application through the student portal.

Scholarship Committee
Caleb University""",
        "scholarships@calebuniversity.edu.ng",
    ),
]


if __name__ == "__main__":
    print("=" * 75)
    print("REAL-WORLD EMAIL CLASSIFICATION TEST")
    print("=" * 75)

    fp_count = 0
    fn_count = 0

    print(f"\n{'='*75}")
    print("REAL PHISHING EMAILS (expect Medium or High)")
    print(f"{'='*75}")
    for name, body, sender in REAL_PHISHING:
        score, tier, count, techs = _analyze(body, sender)
        ok = tier != "Low"
        status = "PASS" if ok else "MISS"
        if not ok:
            fn_count += 1
        print(f"\n  [{status}] {name}")
        print(f"         Score: {score}/100 | Tier: {tier} | Techniques: {count}")
        if techs:
            print(f"         Detected: {', '.join(techs)}")
        if not ok:
            print(f"         *** FALSE NEGATIVE — phishing classified as Low ***")

    print(f"\n{'='*75}")
    print("REAL LEGITIMATE EMAILS (expect Low)")
    print(f"{'='*75}")
    for name, body, sender in REAL_LEGITIMATE:
        score, tier, count, techs = _analyze(body, sender)
        ok = tier == "Low"
        status = "PASS" if ok else "FP!!"
        if not ok:
            fp_count += 1
        print(f"\n  [{status}] {name}")
        print(f"         Score: {score}/100 | Tier: {tier} | Techniques: {count}")
        if techs:
            print(f"         Triggered: {', '.join(techs)}")
        if not ok:
            print(f"         *** FALSE POSITIVE — legitimate classified as {tier} ***")

    total_phish = len(REAL_PHISHING)
    total_legit = len(REAL_LEGITIMATE)
    detected = total_phish - fn_count
    correct_legit = total_legit - fp_count
    total = total_phish + total_legit
    correct = detected + correct_legit
    accuracy = correct / total * 100

    print(f"\n{'='*75}")
    print("RESULTS SUMMARY")
    print(f"{'='*75}")
    print(f"  Phishing detected:     {detected}/{total_phish} ({detected/total_phish*100:.1f}%)")
    print(f"  Legitimate correct:    {correct_legit}/{total_legit} ({correct_legit/total_legit*100:.1f}%)")
    print(f"  False positives:       {fp_count}")
    print(f"  False negatives:       {fn_count}")
    print(f"  Overall accuracy:      {correct}/{total} ({accuracy:.1f}%)")
    print(f"  Detection rate:        {detected/total_phish*100:.1f}%")
    print(f"  False positive rate:   {fp_count/total_legit*100:.1f}%")
    print(f"{'='*75}")
