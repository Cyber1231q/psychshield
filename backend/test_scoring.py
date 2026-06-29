"""Test the recalibrated scoring system."""
import sys
sys.path.insert(0, ".")

from detectors.emotion_detector import detect_emotions
from detectors.manipulation_detector import detect_patterns
from detectors.link_verifier import verify_links
from detectors.risk_scorer import score_email

# TASK 4 — The phishing email that scored 64 MEDIUM before
test_email = """URGENT SECURITY ALERT: Your account has been compromised and will be permanently suspended within 2 hours unless you verify your identity immediately.

We detected unauthorized access from an unknown device in Lagos, Nigeria at 03:42 AM today.

As the IT Security Department, we require all affected users to reset their credentials NOW to prevent further unauthorized access.

Click here immediately to verify: https://paypa1-security.com/verify-account

Failure to act within 2 hours will result in permanent account termination and loss of all stored data. This is your final notice.

Regards,
PayPal Security Team
Official Notice ID: SEC-2026-4471"""

emotion = detect_emotions(test_email)
manip = detect_patterns(test_email)
links = verify_links(test_email, "security-alert@paypa1-security.com")
risk = score_email(emotion, manip, links)

print("=== RECALCULATED RISK ===")
print(f"Emotion score:      {emotion.emotionScore:.3f}")
print(f"Pattern score:      {manip.patternScore:.3f} ({len(manip.techniques)} techniques)")
print(f"Link score:         {links.linkScore:.3f}")
print(f"FINAL SCORE:        {risk.finalScore}/100")
print(f"TIER:               {risk.tier}")
print()
print("Techniques detected:")
for t in manip.techniques:
    print(f"  - {t.name}: {t.evidence}")
print()
print("Old score with linear 3/9: 64 MEDIUM")
print(f"New score with calibrated: {risk.finalScore} {risk.tier}")

# TASK 5 — Safe email must be LOW
print()
print("=== SAFE EMAIL CHECK ===")
safe_email = "Hi team, the meeting is at 3pm tomorrow in Conference Room B. Please bring your progress reports. Thanks, Amaka"
e2 = detect_emotions(safe_email)
m2 = detect_patterns(safe_email)
l2 = verify_links(safe_email, "amaka@calebuniversity.edu.ng")
r2 = score_email(e2, m2, l2)
print(f"Score: {r2.finalScore}/100 | Tier: {r2.tier}")
print(f"Techniques: {len(m2.techniques)}")
print("This MUST be LOW risk")

# TASK 6 — Full test battery
print()
print("=" * 65)
tests = [
    ("High - PayPal",
     "URGENT: Your PayPal account has been permanently suspended due to unauthorized access. Click immediately to verify your identity or lose access: https://paypa1-login.com/verify. This is your final notice from the Security Team.",
     "security@paypa1.com"),
    ("High - CEO fraud",
     "CONFIDENTIAL — from the CEO. We have an urgent situation and need a wire transfer processed immediately. Failure to act now will result in permanent consequences. The bank requires this by deadline. Click here immediately to approve: https://g00gle-docs.xyz/approve",
     "ceo@g00gle-docs.xyz"),
    ("High - IT phishing",
     "IT DEPARTMENT NOTICE: Your account will be permanently blocked due to a security breach. All employees must reset now to prevent unauthorized access. Click immediately: http://192.168.1.1/reset. Failure to comply within 2 hours will result in account termination.",
     "helpdesk@caleb-it.ml"),
    ("Medium - Billing",
     "URGENT: Your payment could not be processed. Your account will be permanently suspended unless you update now. Verify now: https://billing-update.top/pay",
     "billing@billing-update.top"),
    ("Low - Normal",
     "Hi team, meeting at 3pm tomorrow. Please bring your reports.",
     "amaka@calebuniversity.edu.ng"),
    ("Low - Newsletter",
     "Weekly newsletter: upcoming events and announcements. The office party is Friday.",
     "news@calebuniversity.edu.ng"),
]

print(f"{'Expected':<20} {'Score':>6} {'Tier':<8} {'Techniques':>10}")
print("=" * 65)
for expected, body, sender in tests:
    e = detect_emotions(body)
    m = detect_patterns(body)
    l = verify_links(body, sender)
    r = score_email(e, m, l)
    exp_tier = expected.split(" - ")[0]
    status = "PASS" if exp_tier == r.tier else "FAIL"
    print(f"{expected:<20} {r.finalScore:>5}/100 {r.tier:<8} {len(m.techniques):>5}      {status}")
print("=" * 65)
