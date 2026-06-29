"""Risk scorer — combines all detector outputs into a final risk assessment.

Weighted formula: Emotion * 0.40 + Pattern * 0.35 + Link * 0.25
Risk tiers: HIGH >= 65, MEDIUM 35-64, LOW < 35
"""

from models.schemas import (
    EmotionDetectionResult,
    LinkVerificationResult,
    ManipulationResult,
    RiskReport,
    TriggerScores,
)


def score_email(
    emotion: EmotionDetectionResult,
    manipulation: ManipulationResult,
    links: LinkVerificationResult,
) -> RiskReport:
    """Combine detector outputs into a final risk score and tier.

    Args:
        emotion: Output from the emotion detector.
        manipulation: Output from the manipulation detector.
        links: Output from the link verifier.

    Returns:
        RiskReport with weighted score, tier, and human-readable explanation.
    """
    bec_names = {t.name for t in manipulation.techniques}
    is_bec = (
        {"Confidentiality coercion", "Financial urgency"}.issubset(bec_names)
        and links.linkScore < 0.1
    )

    if is_bec:
        composite = (
            emotion.emotionScore * 0.45
            + manipulation.patternScore * 0.55
        )
    else:
        composite = (
            emotion.emotionScore * 0.40
            + manipulation.patternScore * 0.35
            + links.linkScore * 0.25
        )
    final_score = min(round(composite * 100), 100)

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
    if links.linkScore > 0.5:
        flagged = [u.url for u in links.urls if u.riskLevel == "High"]
        if flagged:
            explanation += f"Suspicious URLs detected: {flagged[0]}. "
    if manipulation.techniques:
        explanation += f"Manipulation techniques found: {len(manipulation.techniques)} categories."

    return RiskReport(
        weightedFormula="Emotion×0.40 + Pattern×0.35 + Link×0.25 | HIGH≥65 MED≥35 LOW<35",
        finalScore=final_score,
        tier=tier,
        explanation=explanation,
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
