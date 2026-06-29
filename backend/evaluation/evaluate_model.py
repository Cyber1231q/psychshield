"""Model evaluation script — generates Chapter 4 thesis metrics.

Evaluates all detection modules against test datasets:
  1. Emotion model (TF-IDF + LinearSVC) against GoEmotions test split
  2. Full pipeline (emotion + manipulation + link + risk) against
     synthetic phishing and benign emails
  3. Latency measurement across the full pipeline

Performance targets: accuracy >= 90%, HIGH recall >= 92%, latency <= 3s
"""

import sys
import time

sys.path.insert(0, ".")

import numpy as np
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score

from data.loaders.enron_loader import SYNTHETIC_BENIGN
from data.loaders.goemotions_loader import TRIGGER_MAP, load_goemotions
from detectors.emotion_detector import TRIGGERS, _models, _using_ml, _vectorizer, detect_emotions
from detectors.link_verifier import verify_links
from detectors.manipulation_detector import detect_patterns
from detectors.risk_scorer import score_email

# ── Synthetic phishing emails for full pipeline evaluation ──────

SYNTHETIC_PHISHING: list[dict[str, str]] = [
    {
        "body": "URGENT: Your PayPal account has been compromised. Your account will be permanently suspended unless you verify now: https://paypa1-secure.com/verify",
        "sender": "security@paypa1-secure.com",
    },
    {
        "body": "WARNING: Unauthorized login detected on your Microsoft account. Click immediately to secure your account: https://microsft-login.xyz/auth",
        "sender": "alert@microsft-login.xyz",
    },
    {
        "body": "URGENT: Your Apple ID has been locked due to unauthorized activity. Your account will be permanently terminated unless you verify immediately: https://apple-id-verify.tk/confirm",
        "sender": "noreply@apple-id-verify.tk",
    },
    {
        "body": "CRITICAL: As per IT department policy, all employees must reset their passwords immediately. Failure to comply will result in account termination: https://192.168.1.100/reset",
        "sender": "helpdesk@company-secure.ml",
    },
    {
        "body": "Dear customer, we detected a breach in your Netflix account. Your payment method is at risk. Update now to avoid penalty: https://netfliix-billing.top/update",
        "sender": "billing@netfliix-billing.top",
    },
    {
        "body": "EMERGENCY: Your bank account has been frozen due to suspicious transactions. Verify your identity immediately or face permanent blocking: https://chase-secure.gq/verify",
        "sender": "fraud@chase-secure.gq",
    },
    {
        "body": "Action required: You have been selected for a mandatory compliance review. The director requires your immediate response. Click here now: https://hr-portal-review.cf/submit",
        "sender": "director@hr-portal-review.cf",
    },
    {
        "body": "URGENT NOTICE: Your Amazon account shows unauthorized purchases. Your account will be terminated within 2 hours unless you act now: https://amaz0n-security.ml/dispute",
        "sender": "security@amaz0n-security.ml",
    },
    {
        "body": "Your LinkedIn password has expired. As a security requirement, verify now or your professional network access will be permanently blocked: https://linkedn-verify.ga/reset",
        "sender": "noreply@linkedn-verify.ga",
    },
    {
        "body": "WARNING from the security team: Multiple failed login attempts detected. Your Google account is at risk of suspension. Confirm immediately: https://g00gle-alert.xyz/secure",
        "sender": "security@g00gle-alert.xyz",
    },
    {
        "body": "URGENT: Please help, I am desperate. My late husband left funds that the bank will freeze permanently. I urgently need your assistance immediately or the money will be blocked: https://charity-help.tk/donate",
        "sender": "help@charity-help.tk",
    },
    {
        "body": "URGENT WARNING: You agreed to our terms and your payment of $499 is critically overdue. Pay immediately to avoid permanent account suspension and penalty: https://billing-service.click/pay",
        "sender": "billing@billing-service.click",
    },
    {
        "body": "Official notice from management headquarters: All staff are required to complete mandatory compliance training immediately or face disciplinary action: https://corp-training.loan/enroll",
        "sender": "compliance@corp-training.loan",
    },
    {
        "body": "Your colleague referred you for an exclusive offer. Only selected users qualify. Claim your verified reward before the deadline expires: https://reward-claim.gq/get",
        "sender": "rewards@reward-claim.gq",
    },
    {
        "body": "DANGER: Your Dropbox files are compromised. Attackers have breached your account. Act immediately to prevent permanent data loss: https://dr0pbox-recover.xyz/files",
        "sender": "alert@dr0pbox-recover.xyz",
    },
]


def evaluate_emotion_model() -> dict:
    """Evaluate the emotion model against GoEmotions test split.

    Returns:
        Dict with per-trigger and overall metrics.
    """
    print("=" * 60)
    print("SECTION 1: EMOTION MODEL EVALUATION (GoEmotions Test Set)")
    print("=" * 60)

    if not _using_ml:
        print("WARNING: ML model not loaded — cannot evaluate")
        return {}

    _, test_df = load_goemotions()
    X_test = _vectorizer.transform(test_df["text"])

    results: dict[str, dict] = {}
    all_y_true: list = []
    all_y_pred: list = []

    print(f"\nTest samples: {len(test_df)}")
    print(f"{'Trigger':<12} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}")
    print("-" * 56)

    for trigger in TRIGGERS:
        clf = _models[trigger]
        y_true = test_df[trigger].values
        y_pred = clf.predict(X_test)

        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        results[trigger] = {
            "accuracy": round(acc * 100, 2),
            "precision": round(prec * 100, 2),
            "recall": round(rec * 100, 2),
            "f1": round(f1 * 100, 2),
        }

        all_y_true.extend(y_true)
        all_y_pred.extend(y_pred)

        print(f"{trigger:<12} {acc:>9.2%} {prec:>9.2%} {rec:>9.2%} {f1:>9.2%}")

    overall_acc = accuracy_score(all_y_true, all_y_pred)
    overall_prec = precision_score(all_y_true, all_y_pred, zero_division=0)
    overall_rec = recall_score(all_y_true, all_y_pred, zero_division=0)
    overall_f1 = f1_score(all_y_true, all_y_pred, zero_division=0)

    print("-" * 56)
    print(f"{'OVERALL':<12} {overall_acc:>9.2%} {overall_prec:>9.2%} {overall_rec:>9.2%} {overall_f1:>9.2%}")

    target_met = overall_acc >= 0.90
    print(f"\nAccuracy target (>= 90%): {'PASSED' if target_met else 'FAILED'} ({overall_acc:.2%})")

    return {
        "per_trigger": results,
        "overall_accuracy": round(overall_acc * 100, 2),
        "overall_precision": round(overall_prec * 100, 2),
        "overall_recall": round(overall_rec * 100, 2),
        "overall_f1": round(overall_f1 * 100, 2),
    }


def evaluate_full_pipeline() -> dict:
    """Evaluate the full detection pipeline on phishing vs benign emails.

    Returns:
        Dict with pipeline classification metrics.
    """
    print("\n" + "=" * 60)
    print("SECTION 2: FULL PIPELINE EVALUATION (Phishing vs Benign)")
    print("=" * 60)

    y_true: list[int] = []
    y_pred: list[int] = []
    tiers_phishing: list[str] = []
    tiers_benign: list[str] = []

    print(f"\nPhishing samples: {len(SYNTHETIC_PHISHING)}")
    print(f"Benign samples:   {len(SYNTHETIC_BENIGN)}")
    print()

    print("--- Phishing Emails ---")
    for i, email in enumerate(SYNTHETIC_PHISHING):
        emotion = detect_emotions(email["body"])
        manipulation = detect_patterns(email["body"])
        links = verify_links(email["body"], email["sender"])
        risk = score_email(emotion, manipulation, links)

        is_flagged = 1 if risk.tier in ("High", "Medium") else 0
        y_true.append(1)
        y_pred.append(is_flagged)
        tiers_phishing.append(risk.tier)
        status = "CORRECT" if is_flagged == 1 else "MISSED"
        print(f"  [{status}] #{i+1:02d} Score={risk.finalScore:>3}/100 Tier={risk.tier:<6} | {email['body'][:60]}...")

    print("\n--- Benign Emails ---")
    for i, body in enumerate(SYNTHETIC_BENIGN):
        emotion = detect_emotions(body)
        manipulation = detect_patterns(body)
        links = verify_links(body)
        risk = score_email(emotion, manipulation, links)

        is_flagged = 1 if risk.tier in ("High", "Medium") else 0
        y_true.append(0)
        y_pred.append(is_flagged)
        tiers_benign.append(risk.tier)
        status = "CORRECT" if is_flagged == 0 else "FALSE+"
        print(f"  [{status}] #{i+1:02d} Score={risk.finalScore:>3}/100 Tier={risk.tier:<6} | {body[:60]}...")

    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)

    high_count = tiers_phishing.count("High")
    med_count = tiers_phishing.count("Medium")
    low_count = tiers_phishing.count("Low")
    high_recall = (high_count + med_count) / len(SYNTHETIC_PHISHING) if SYNTHETIC_PHISHING else 0

    benign_low = tiers_benign.count("Low")
    false_positives = len(SYNTHETIC_BENIGN) - benign_low

    print(f"\n{'Metric':<25} {'Value':>10}")
    print("-" * 37)
    print(f"{'Pipeline Accuracy':<25} {acc:>9.2%}")
    print(f"{'Precision':<25} {prec:>9.2%}")
    print(f"{'Recall (Detection Rate)':<25} {rec:>9.2%}")
    print(f"{'F1 Score':<25} {f1:>9.2%}")
    print(f"{'Phishing -> High':<25} {high_count:>6}/{len(SYNTHETIC_PHISHING)}")
    print(f"{'Phishing -> Medium':<25} {med_count:>6}/{len(SYNTHETIC_PHISHING)}")
    print(f"{'Phishing -> Low (missed)':<25} {low_count:>6}/{len(SYNTHETIC_PHISHING)}")
    print(f"{'Benign -> Low (correct)':<25} {benign_low:>6}/{len(SYNTHETIC_BENIGN)}")
    print(f"{'False Positives':<25} {false_positives:>6}/{len(SYNTHETIC_BENIGN)}")

    recall_met = high_recall >= 0.92
    print(f"\nHIGH recall target (>= 92%): {'PASSED' if recall_met else 'FAILED'} ({high_recall:.2%})")

    return {
        "accuracy": round(acc * 100, 2),
        "precision": round(prec * 100, 2),
        "recall": round(rec * 100, 2),
        "f1": round(f1 * 100, 2),
        "high_recall": round(high_recall * 100, 2),
        "phishing_tiers": {"High": high_count, "Medium": med_count, "Low": low_count},
        "benign_correct": benign_low,
        "false_positives": false_positives,
    }


def evaluate_latency() -> dict:
    """Measure average latency across the full pipeline.

    Returns:
        Dict with latency statistics.
    """
    print("\n" + "=" * 60)
    print("SECTION 3: LATENCY EVALUATION")
    print("=" * 60)

    test_emails = SYNTHETIC_PHISHING[:5] + [
        {"body": b, "sender": ""} for b in SYNTHETIC_BENIGN[:5]
    ]

    latencies: list[float] = []
    for email in test_emails:
        start = time.perf_counter()
        emotion = detect_emotions(email["body"])
        manipulation = detect_patterns(email["body"])
        links = verify_links(email["body"], email.get("sender", ""))
        _ = score_email(emotion, manipulation, links)
        elapsed = time.perf_counter() - start
        latencies.append(elapsed)

    avg_ms = np.mean(latencies) * 1000
    max_ms = np.max(latencies) * 1000
    min_ms = np.min(latencies) * 1000
    p95_ms = np.percentile(latencies, 95) * 1000

    print(f"\nSamples tested: {len(test_emails)}")
    print(f"{'Metric':<25} {'Value':>10}")
    print("-" * 37)
    print(f"{'Average latency':<25} {avg_ms:>7.1f} ms")
    print(f"{'Min latency':<25} {min_ms:>7.1f} ms")
    print(f"{'Max latency':<25} {max_ms:>7.1f} ms")
    print(f"{'P95 latency':<25} {p95_ms:>7.1f} ms")

    target_met = avg_ms <= 3000
    print(f"\nLatency target (<= 3000ms): {'PASSED' if target_met else 'FAILED'} ({avg_ms:.1f}ms)")

    return {
        "avg_ms": round(avg_ms, 1),
        "min_ms": round(min_ms, 1),
        "max_ms": round(max_ms, 1),
        "p95_ms": round(p95_ms, 1),
    }


def print_summary(emotion_results: dict, pipeline_results: dict, latency_results: dict) -> None:
    """Print the final summary table for Chapter 4."""
    print("\n" + "=" * 60)
    print("CHAPTER 4 — RESULTS SUMMARY TABLE")
    print("=" * 60)

    print(f"\n{'Metric':<35} {'Result':>10} {'Target':>10} {'Status':>8}")
    print("-" * 67)

    emo_acc = emotion_results.get("overall_accuracy", 0)
    print(f"{'Emotion Model Accuracy':<35} {emo_acc:>9.2f}% {'>= 90%':>10} {'PASS' if emo_acc >= 90 else 'FAIL':>8}")

    emo_prec = emotion_results.get("overall_precision", 0)
    print(f"{'Emotion Model Precision':<35} {emo_prec:>9.2f}% {'—':>10} {'—':>8}")

    emo_rec = emotion_results.get("overall_recall", 0)
    print(f"{'Emotion Model Recall':<35} {emo_rec:>9.2f}% {'—':>10} {'—':>8}")

    emo_f1 = emotion_results.get("overall_f1", 0)
    print(f"{'Emotion Model F1':<35} {emo_f1:>9.2f}% {'—':>10} {'—':>8}")

    pip_acc = pipeline_results.get("accuracy", 0)
    print(f"{'Pipeline Accuracy':<35} {pip_acc:>9.2f}% {'>= 90%':>10} {'PASS' if pip_acc >= 90 else 'FAIL':>8}")

    pip_rec = pipeline_results.get("high_recall", 0)
    print(f"{'HIGH Recall (Detection Rate)':<35} {pip_rec:>9.2f}% {'>= 92%':>10} {'PASS' if pip_rec >= 92 else 'FAIL':>8}")

    pip_f1 = pipeline_results.get("f1", 0)
    print(f"{'Pipeline F1':<35} {pip_f1:>9.2f}% {'—':>10} {'—':>8}")

    fp = pipeline_results.get("false_positives", 0)
    print(f"{'False Positives':<35} {fp:>10} {'0':>10} {'PASS' if fp == 0 else 'WARN':>8}")

    avg_lat = latency_results.get("avg_ms", 0)
    print(f"{'Avg Latency':<35} {avg_lat:>7.1f} ms {'<= 3000':>10} {'PASS' if avg_lat <= 3000 else 'FAIL':>8}")

    p95_lat = latency_results.get("p95_ms", 0)
    print(f"{'P95 Latency':<35} {p95_lat:>7.1f} ms {'—':>10} {'—':>8}")

    print("-" * 67)

    all_pass = emo_acc >= 90 and pip_acc >= 90 and pip_rec >= 92 and avg_lat <= 3000
    print(f"\nOVERALL VERDICT: {'ALL TARGETS MET' if all_pass else 'SOME TARGETS NOT MET'}")

    print("\n--- Per-Trigger Emotion Accuracy ---")
    print(f"{'Trigger':<12} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}")
    print("-" * 56)
    for trigger in TRIGGERS:
        t = emotion_results.get("per_trigger", {}).get(trigger, {})
        print(f"{trigger:<12} {t.get('accuracy', 0):>9.2f}% {t.get('precision', 0):>9.2f}% {t.get('recall', 0):>9.2f}% {t.get('f1', 0):>9.2f}%")


if __name__ == "__main__":
    print("PsychShield Model Evaluation")
    print(f"Model: {'TF-IDF + LinearSVC (GoEmotions)' if _using_ml else 'Keyword fallback'}")
    print()

    emotion_results = evaluate_emotion_model()
    pipeline_results = evaluate_full_pipeline()
    latency_results = evaluate_latency()
    print_summary(emotion_results, pipeline_results, latency_results)
