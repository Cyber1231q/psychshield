"""False positive and classification accuracy test suite.

Tests the full pipeline against:
  - Legitimate business emails (MUST score Low)
  - Legitimate automated notifications (MUST score Low)
  - Obvious phishing emails (MUST score Medium or High)
  - Subtle phishing emails (MUST score Medium or High)
  - Edge cases that look suspicious but are legitimate
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
    return r.finalScore, r.tier, len(m.techniques)


# ═══════════════════════════════════════════════════════════════
# GROUP 1: LEGITIMATE BUSINESS EMAILS — ALL MUST BE LOW
# ═══════════════════════════════════════════════════════════════

LEGIT_BUSINESS = [
    ("Team meeting", "Hi team, the project meeting is scheduled for Friday at 2pm. Please bring your progress reports.", "manager@calebuniversity.edu.ng"),
    ("Leave request", "Reminder: Annual leave requests must be submitted by end of the month.", "hr@calebuniversity.edu.ng"),
    ("Quarterly review", "The quarterly review is next week. Please prepare your department summaries.", "director@calebuniversity.edu.ng"),
    ("Client update", "Just checking in on the status of the client deliverable. Let me know if you need support.", "lead@calebuniversity.edu.ng"),
    ("Congratulations", "Congratulations to everyone on completing the milestone. Great work this quarter.", "ceo@calebuniversity.edu.ng"),
    ("Room booking", "The conference room on the third floor is booked from 9am to 11am on Monday.", "admin@calebuniversity.edu.ng"),
    ("Timeline update", "Please find attached the updated project timeline for your review and feedback.", "pm@calebuniversity.edu.ng"),
    ("Training session", "Training session for the new HR system is scheduled for Tuesday afternoon.", "training@calebuniversity.edu.ng"),
    ("New printer", "The new printer has been installed near reception on the second floor.", "facilities@calebuniversity.edu.ng"),
    ("Weekly update", "Weekly update: upcoming deadlines and team announcements are listed below.", "team@calebuniversity.edu.ng"),
    ("Reschedule", "Can we reschedule our 1-on-1 to Thursday? I have a conflict on Wednesday.", "boss@calebuniversity.edu.ng"),
    ("IT maintenance", "The IT team will be performing maintenance on Sunday night from 10pm to 2am.", "it@calebuniversity.edu.ng"),
    ("Expense reports", "Please submit your expense reports before the end of the financial quarter.", "finance@calebuniversity.edu.ng"),
    ("Holiday notice", "The office will be closed on the public holiday next Monday.", "admin@calebuniversity.edu.ng"),
    ("Promotion", "We are pleased to announce the promotion of three team members this month.", "hr@calebuniversity.edu.ng"),
    ("Budget approved", "The budget proposal for Q4 has been reviewed and approved by finance.", "cfo@calebuniversity.edu.ng"),
    ("Performance review", "The annual performance review cycle begins next month. Watch for calendar invites.", "hr@calebuniversity.edu.ng"),
    ("Compliance training", "All staff are reminded to complete the mandatory compliance training by Friday.", "compliance@calebuniversity.edu.ng"),
    ("Lunch plans", "The team lunch is confirmed for Thursday at 1pm at the usual restaurant.", "team@calebuniversity.edu.ng"),
    ("Fire drill", "Reminder to all staff: fire drill scheduled for Wednesday at 11am.", "safety@calebuniversity.edu.ng"),
]

LEGIT_NOTIFICATIONS = [
    ("Shipping update", "Your order #12345 has been shipped and will arrive by Thursday.", "orders@amazon.com"),
    ("Flight confirmation", "Your flight to Abuja on July 5th is confirmed. Check-in opens 24 hours before departure.", "bookings@airline.com"),
    ("Newsletter", "This week in tech: new developments in AI security and cybersecurity trends.", "newsletter@techblog.com"),
    ("Calendar invite", "You have been invited to Product Review on Monday at 10am. Accept or decline.", "calendar@google.com"),
    ("Receipt", "Thank you for your purchase of $25.99. Your receipt is attached.", "noreply@store.com"),
    ("Welcome email", "Welcome to PsychShield! Your account has been created successfully.", "noreply@psychshield.test"),
    ("Password changed", "Your password was changed successfully. If this was not you, contact support.", "security@bank.com"),
    ("Subscription renewal", "Your annual subscription renews on July 15. No action needed.", "billing@service.com"),
]

# Emails that use trigger words but are clearly legitimate
LEGIT_EDGE_CASES = [
    ("IT policy email", "Per official IT department policy, all employees must complete the security awareness training by end of month. This is a mandatory annual requirement.", "it-security@calebuniversity.edu.ng"),
    ("Deadline reminder", "Urgent reminder: The deadline for thesis submission is next Friday. Please ensure all documents are uploaded to the portal.", "registry@calebuniversity.edu.ng"),
    ("Account maintenance", "Your university email account will be temporarily unavailable during scheduled maintenance this weekend. No action is required on your part.", "helpdesk@calebuniversity.edu.ng"),
    ("Security advisory", "Security advisory: We have detected increased phishing attempts targeting staff. Please be vigilant and report suspicious emails.", "ciso@calebuniversity.edu.ng"),
    ("Charity event", "Please help support the annual charity drive. Your kindness and assistance can make a difference for those in need.", "charity@calebuniversity.edu.ng"),
]


# ═══════════════════════════════════════════════════════════════
# GROUP 2: PHISHING EMAILS — ALL MUST BE MEDIUM OR HIGH
# ═══════════════════════════════════════════════════════════════

OBVIOUS_PHISHING = [
    ("PayPal suspend", "URGENT: Your PayPal account has been suspended. Click immediately to verify: https://paypa1-login.com/verify", "security@paypa1-login.com"),
    ("Microsoft alert", "WARNING: Unauthorized login detected. Your account will be terminated unless you verify now: https://microsft-secure.xyz/auth", "alert@microsft-secure.xyz"),
    ("Apple locked", "URGENT: Your Apple ID has been locked due to unauthorized activity. Verify immediately or lose access permanently: https://apple-verify.tk/confirm", "noreply@apple-verify.tk"),
    ("IT reset", "CRITICAL: IT department requires all employees to reset passwords immediately. Failure to comply results in account termination: http://192.168.1.100/reset", "helpdesk@company-it.ml"),
    ("Netflix breach", "Dear customer, we detected a breach in your Netflix account. Update now to avoid penalty: https://netfliix-billing.top/update", "billing@netfliix-billing.top"),
    ("Bank frozen", "EMERGENCY: Your bank account has been frozen. Verify your identity immediately or face permanent blocking: https://chase-secure.gq/verify", "fraud@chase-secure.gq"),
    ("Amazon terminate", "URGENT: Your Amazon account shows unauthorized purchases. Account will be terminated within 2 hours: https://amaz0n-security.ml/dispute", "security@amaz0n-security.ml"),
    ("Google suspend", "WARNING from security team: Multiple failed login attempts. Your Google account is at risk of suspension. Confirm now: https://g00gle-alert.xyz/secure", "security@g00gle-alert.xyz"),
    ("Dropbox compromised", "DANGER: Your Dropbox files are compromised. Attackers have breached your account. Act immediately: https://dr0pbox-recover.xyz/files", "alert@dr0pbox-recover.xyz"),
    ("LinkedIn expired", "Your LinkedIn password has expired. Verify now or your access will be permanently blocked: https://linkedn-verify.ga/reset", "noreply@linkedn-verify.ga"),
]

SUBTLE_PHISHING = [
    ("Soft account verify", "Dear user, we noticed unusual sign-in activity on your account. For your security, please verify your identity: https://secure-login.xyz/verify", "security@secure-login.xyz"),
    ("Routine check", "This is a routine security check. We detected suspicious activity and your access will be removed unless you update your information: https://account-check.tk/update", "admin@account-check.tk"),
    ("Compliance scam", "You have been selected for a mandatory compliance review. The director requires your immediate response. Click here now: https://hr-review.cf/submit", "director@hr-review.cf"),
    ("Prize scam", "Your colleague referred you for an exclusive offer. Only selected users qualify. Claim your verified reward before the deadline: https://reward-claim.gq/get", "rewards@reward-claim.gq"),
    ("Billing threat", "URGENT WARNING: Your payment is critically overdue. Pay immediately to avoid permanent account suspension and penalty: https://billing-service.click/pay", "billing@billing-service.click"),
]


def test_legit_business_all_low():
    failures = []
    for name, body, sender in LEGIT_BUSINESS:
        score, tier, techs = _analyze(body, sender)
        if tier != "Low":
            failures.append(f"FALSE POSITIVE: '{name}' scored {score} ({tier}), techniques={techs}")
    assert not failures, "\n".join(failures)


def test_legit_notifications_all_low():
    failures = []
    for name, body, sender in LEGIT_NOTIFICATIONS:
        score, tier, techs = _analyze(body, sender)
        if tier != "Low":
            failures.append(f"FALSE POSITIVE: '{name}' scored {score} ({tier}), techniques={techs}")
    assert not failures, "\n".join(failures)


def test_legit_edge_cases_all_low():
    failures = []
    for name, body, sender in LEGIT_EDGE_CASES:
        score, tier, techs = _analyze(body, sender)
        if tier != "Low":
            failures.append(f"FALSE POSITIVE: '{name}' scored {score} ({tier}), techniques={techs}")
    assert not failures, "\n".join(failures)


def test_obvious_phishing_detected():
    failures = []
    for name, body, sender in OBVIOUS_PHISHING:
        score, tier, techs = _analyze(body, sender)
        if tier == "Low":
            failures.append(f"MISSED: '{name}' scored {score} ({tier}), techniques={techs}")
    assert not failures, "\n".join(failures)


def test_subtle_phishing_detected():
    failures = []
    for name, body, sender in SUBTLE_PHISHING:
        score, tier, techs = _analyze(body, sender)
        if tier == "Low":
            failures.append(f"MISSED: '{name}' scored {score} ({tier}), techniques={techs}")
    assert not failures, "\n".join(failures)


if __name__ == "__main__":
    print("=" * 70)
    print("PSYCHSHIELD FALSE POSITIVE & CLASSIFICATION TEST")
    print("=" * 70)

    all_pass = True

    print("\n--- LEGITIMATE BUSINESS (expect Low) ---")
    for name, body, sender in LEGIT_BUSINESS:
        score, tier, techs = _analyze(body, sender)
        status = "PASS" if tier == "Low" else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  [{status}] {score:>3}/100 {tier:<6} techs={techs} | {name}")

    print("\n--- LEGITIMATE NOTIFICATIONS (expect Low) ---")
    for name, body, sender in LEGIT_NOTIFICATIONS:
        score, tier, techs = _analyze(body, sender)
        status = "PASS" if tier == "Low" else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  [{status}] {score:>3}/100 {tier:<6} techs={techs} | {name}")

    print("\n--- LEGITIMATE EDGE CASES (expect Low) ---")
    for name, body, sender in LEGIT_EDGE_CASES:
        score, tier, techs = _analyze(body, sender)
        status = "PASS" if tier == "Low" else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  [{status}] {score:>3}/100 {tier:<6} techs={techs} | {name}")

    print("\n--- OBVIOUS PHISHING (expect Medium/High) ---")
    for name, body, sender in OBVIOUS_PHISHING:
        score, tier, techs = _analyze(body, sender)
        status = "PASS" if tier != "Low" else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  [{status}] {score:>3}/100 {tier:<6} techs={techs} | {name}")

    print("\n--- SUBTLE PHISHING (expect Medium/High) ---")
    for name, body, sender in SUBTLE_PHISHING:
        score, tier, techs = _analyze(body, sender)
        status = "PASS" if tier != "Low" else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  [{status}] {score:>3}/100 {tier:<6} techs={techs} | {name}")

    print("\n" + "=" * 70)
    legit_total = len(LEGIT_BUSINESS) + len(LEGIT_NOTIFICATIONS) + len(LEGIT_EDGE_CASES)
    phish_total = len(OBVIOUS_PHISHING) + len(SUBTLE_PHISHING)
    print(f"Legitimate emails tested: {legit_total}")
    print(f"Phishing emails tested:   {phish_total}")
    print(f"OVERALL: {'ALL PASS' if all_pass else 'FAILURES DETECTED'}")
    print("=" * 70)
