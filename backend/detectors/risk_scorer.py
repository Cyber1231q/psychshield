"""Risk scorer — combines all detector outputs into a final risk assessment.

Weighted formula: Emotion×0.35 + Pattern×0.30 + Link×0.20 + Sender×0.15
BEC formula (link excluded — BEC emails rarely carry a URL):
    Emotion×0.40 + Pattern×0.45 + Sender×0.15
Risk tiers: HIGH >= 60, MEDIUM 40-59, LOW < 40

When no sender was available to check (sender=None), the Sender slot is
dropped and the remaining weights are renormalized to sum back to 1.0 —
otherwise a plain content-only analysis (very common: pasted text with no
"From" line) would silently forfeit 15% of its scoring budget and read as
less risky than it actually is. See _weighted_composite below.

The Sender component is derived from SenderVerification (typosquat,
SPF/DKIM/DMARC, and domain registration age) — see _sender_risk_score
below. It replaces an earlier domain-age floor mechanic that always fired
at "unverifiable" because no domain-age lookup was ever actually
implemented (domainAgeDays was a permanent None stub); a real, gradable
sender signal is a strict upgrade.
"""

from typing import Optional

from models.schemas import (
    EmotionDetectionResult,
    LinkVerificationResult,
    ManipulationResult,
    RiskReport,
    SenderVerification,
    TriggerScores,
)

# UNKNOWN counts for only a small amount of risk — "couldn't verify" (e.g. no
# DNS record, or a paste-mode analysis with no delivery headers to check) is
# not the same as "confirmed malicious", and shouldn't be scored as if it were.
_SENDER_AUTH_RISK = {"FAIL": 1.0, "UNKNOWN": 0.15, "PASS": 0.0}

_WEIGHTS = {"emotion": 0.35, "pattern": 0.30, "link": 0.20, "sender": 0.15}
_BEC_WEIGHTS = {"emotion": 0.40, "pattern": 0.45, "sender": 0.15}
_LABELS = {"emotion": "Emotion", "pattern": "Pattern", "link": "Link", "sender": "Sender"}


def _domain_age_risk(domain_age_days: Optional[int]) -> float:
    """Convert a WHOIS domain age into a 0.0-1.0 risk contribution.

    A domain registered in the last month is a classic phishing indicator
    (throwaway infrastructure spun up for a single campaign); a domain
    that's been around for a quarter or more is treated as established.
    None (WHOIS unavailable — rate limits, privacy-protected registration,
    an unsupported TLD, a timeout) is weighed the same as an UNKNOWN
    SPF/DKIM/DMARC result: weak evidence, not proof of anything. This is
    the exact distinction the old domain-age floor got wrong — it treated
    "couldn't check" as "suspicious enough to floor the score" outright.
    """
    if domain_age_days is None:
        return 0.15
    if domain_age_days < 30:
        return 1.0
    if domain_age_days < 90:
        return 0.5
    return 0.0


def _sender_risk_score(sender: Optional[SenderVerification]) -> float:
    """Convert sender verification signals into a 0.0-1.0 risk contribution.

    Typosquatting is decisive on its own (confirmed brand impersonation).
    Otherwise DMARC and domain age carry the most weight: DMARC is the
    policy layer that governs what happens when SPF/DKIM disagree with the
    visible From: domain, and domain age is the strongest single signal
    among the DNS-derived checks (SPF/DMARC presence is common even among
    disposable domains; a domain registered days ago is not).
    """
    if sender is None:
        return 0.0
    if sender.typosquatted:
        return 1.0
    spf_risk = _SENDER_AUTH_RISK.get(sender.spf, 0.15)
    dkim_risk = _SENDER_AUTH_RISK.get(sender.dkim, 0.15)
    dmarc_risk = _SENDER_AUTH_RISK.get(sender.dmarc, 0.15)
    age_risk = _domain_age_risk(sender.domainAgeDays)
    return min(
        1.0,
        spf_risk * 0.2 + dkim_risk * 0.2 + dmarc_risk * 0.3 + age_risk * 0.3,
    )


def _weighted_composite(components: dict, weights: dict) -> tuple[float, str]:
    """Weighted average over only the components actually present.

    Weights are renormalized to sum to 1.0 across present components, so a
    missing signal (e.g. no sender to check) never deflates the score —
    it's excluded from the average rather than averaged in as a zero.
    """
    active = {k: weights[k] for k in components}
    total = sum(active.values())
    normalized = {k: w / total for k, w in active.items()}
    composite = sum(components[k] * normalized[k] for k in components)
    formula = " + ".join(
        f"{_LABELS[k]}×{normalized[k]:.2f}" for k in ("emotion", "pattern", "link", "sender") if k in normalized
    )
    return composite, formula


def score_email(
    emotion: EmotionDetectionResult,
    manipulation: ManipulationResult,
    links: LinkVerificationResult,
    sender: Optional[SenderVerification] = None,
) -> RiskReport:
    """Combine detector outputs into a final risk score and tier.

    Args:
        emotion: Output from the emotion detector.
        manipulation: Output from the manipulation detector.
        links: Output from the link verifier.
        sender: Output from verify_sender(), or None if no sender address
            was available to check.

    Returns:
        RiskReport with weighted score, tier, explanation, and optional
        scoreReason describing why the sender signal was notable.
    """
    bec_names = {t.name for t in manipulation.techniques}
    is_bec = (
        {"Confidentiality coercion", "Financial urgency"}.issubset(bec_names)
        and links.linkScore < 0.1
    )

    components = {"emotion": emotion.emotionScore, "pattern": manipulation.patternScore}
    if not is_bec:
        components["link"] = links.linkScore
    if sender is not None:
        components["sender"] = _sender_risk_score(sender)

    weights = _BEC_WEIGHTS if is_bec else _WEIGHTS
    composite, formula = _weighted_composite(components, weights)
    weighted_formula = f"{formula}{' (BEC)' if is_bec else ''} | HIGH≥60 MED≥40 LOW<40"
    final_score = min(round(composite * 100), 100)

    score_reason: Optional[str] = None
    if sender is not None and sender.typosquatted:
        score_reason = "Sender domain closely resembles a trusted brand (typosquatting)"
    elif sender is not None and components["sender"] >= 0.5:
        score_reason = "Sender authentication failed (SPF/DKIM/DMARC)"

    if final_score >= 60:
        tier = "High"
    elif final_score >= 40:
        tier = "Medium"
    else:
        tier = "Low"

    highest_emotion = max(emotion.categoryScores, key=lambda x: x.score)

    explanation = (
        f"This email scored {final_score}/100 and is classified as {tier.upper()} risk. "
        f"Dominant psychological trigger: {highest_emotion.category} "
        f"({highest_emotion.score:.0%}). "
    )
    if score_reason:
        explanation += f"{score_reason}. "
    if links.linkScore > 0.5:
        flagged = [u.url for u in links.urls if u.riskLevel == "High"]
        if flagged:
            explanation += f"Suspicious URLs detected: {flagged[0]}. "
    if manipulation.techniques:
        explanation += f"Manipulation techniques found: {len(manipulation.techniques)} categories."

    return RiskReport(
        weightedFormula=weighted_formula,
        finalScore=final_score,
        tier=tier,
        explanation=explanation,
        scoreReason=score_reason,
    )


def get_trigger_scores(emotion: EmotionDetectionResult) -> TriggerScores:
    """Extract per-trigger percentage scores from emotion category scores.

    Args:
        emotion: Output from the emotion detector.

    Returns:
        TriggerScores with each trigger as a 0-100 percentage.
    """
    scores = {s.category: round(s.score * 100, 1) for s in emotion.categoryScores}
    return TriggerScores(
        urgency=scores.get("urgency", 0),
        fear=scores.get("fear", 0),
        authority=scores.get("authority", 0),
        trust=scores.get("trust", 0),
        pity=scores.get("pity", 0),
    )
