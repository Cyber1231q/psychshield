"""Tests for the risk scorer module."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from detectors.risk_scorer import score_email, get_trigger_scores
from models.schemas import (
    EmotionCategoryScore,
    EmotionDetectionResult,
    LinkVerificationResult,
    ManipulationResult,
    SenderVerification,
    TriggerScores,
)


def _make_sender(typosquatted=False, spf="UNKNOWN", dkim="UNKNOWN", dmarc="UNKNOWN", domain_age_days=None):
    return SenderVerification(
        **{"from": "test@example.com"},
        displayName="test",
        domain="example.com",
        typosquatted=typosquatted,
        spf=spf,
        dkim=dkim,
        dmarc=dmarc,
        domainAgeDays=domain_age_days,
    )


def _make_emotion(score: float) -> EmotionDetectionResult:
    return EmotionDetectionResult(
        model="test",
        categoryScores=[
            EmotionCategoryScore(category="urgency", score=score),
            EmotionCategoryScore(category="fear", score=score),
            EmotionCategoryScore(category="authority", score=score),
            EmotionCategoryScore(category="trust", score=score),
            EmotionCategoryScore(category="pity", score=score),
        ],
        emotionScore=score,
        summary="test",
    )


def _make_manipulation(score: float) -> ManipulationResult:
    return ManipulationResult(
        model="test", patternScore=score, techniques=[]
    )


def _make_links(score: float) -> LinkVerificationResult:
    return LinkVerificationResult(model="test", linkScore=score, urls=[])


def test_high_inputs_produce_high_tier():
    risk = score_email(_make_emotion(0.9), _make_manipulation(0.9), _make_links(0.9))
    assert risk.tier == "High"
    assert risk.finalScore > 70


def test_low_inputs_produce_low_tier():
    risk = score_email(_make_emotion(0.1), _make_manipulation(0.1), _make_links(0.1))
    assert risk.tier == "Low"
    assert risk.finalScore < 40


def test_formula_is_correct():
    """Equal inputs across every present signal must collapse to that same
    value, since weights are renormalized to sum to 1.0 over whichever
    signals are actually present (no sender here, so Emotion/Pattern/Link
    renormalize amongst themselves)."""
    risk = score_email(_make_emotion(0.8), _make_manipulation(0.8), _make_links(0.8))
    assert risk.finalScore == 80


def test_score_always_0_to_100():
    for val in [0.0, 0.1, 0.5, 0.99, 1.0]:
        risk = score_email(_make_emotion(val), _make_manipulation(val), _make_links(val))
        assert 0 <= risk.finalScore <= 100


def test_medium_tier_at_boundary():
    risk = score_email(_make_emotion(0.5), _make_manipulation(0.5), _make_links(0.5))
    assert risk.tier == "Medium"
    assert 40 <= risk.finalScore <= 70


def test_zero_inputs_produce_zero():
    risk = score_email(_make_emotion(0.0), _make_manipulation(0.0), _make_links(0.0))
    assert risk.finalScore == 0
    assert risk.tier == "Low"


def test_explanation_contains_score():
    risk = score_email(_make_emotion(0.5), _make_manipulation(0.5), _make_links(0.5))
    assert str(risk.finalScore) in risk.explanation


def test_weighted_formula_string_with_sender():
    risk = score_email(
        _make_emotion(0.5), _make_manipulation(0.5), _make_links(0.5),
        sender=_make_sender(),
    )
    assert "0.35" in risk.weightedFormula
    assert "0.30" in risk.weightedFormula
    assert "0.20" in risk.weightedFormula
    assert "0.15" in risk.weightedFormula


def test_weighted_formula_string_no_sender_renormalizes():
    """Without a sender, the Sender term drops and the rest renormalize to 1.0."""
    risk = score_email(_make_emotion(0.5), _make_manipulation(0.5), _make_links(0.5))
    assert "Sender" not in risk.weightedFormula
    assert "Emotion" in risk.weightedFormula
    assert "Pattern" in risk.weightedFormula
    assert "Link" in risk.weightedFormula


def test_get_trigger_scores_returns_percentages():
    emotion = _make_emotion(0.75)
    triggers = get_trigger_scores(emotion)
    assert triggers.urgency == 75.0
    assert triggers.fear == 75.0
    assert triggers.authority == 75.0
    assert triggers.trust == 75.0
    assert triggers.pity == 75.0


def test_get_trigger_scores_zero():
    emotion = _make_emotion(0.0)
    triggers = get_trigger_scores(emotion)
    assert triggers.urgency == 0
    assert triggers.fear == 0


# ── Sender verification tests ────────────────────────────────────────────────


def test_typosquatted_sender_boosts_score():
    """A typosquatted sender domain must raise the score above the no-sender baseline."""
    baseline = score_email(_make_emotion(0.1), _make_manipulation(0.1), _make_links(0.1))
    risk = score_email(
        _make_emotion(0.1), _make_manipulation(0.1), _make_links(0.1),
        sender=_make_sender(typosquatted=True),
    )
    assert risk.finalScore > baseline.finalScore
    assert risk.scoreReason == "Sender domain closely resembles a trusted brand (typosquatting)"


def test_failed_auth_sender_sets_reason():
    """SPF/DKIM/DMARC all failing must set a scoreReason and raise the score."""
    baseline = score_email(_make_emotion(0.1), _make_manipulation(0.1), _make_links(0.1))
    risk = score_email(
        _make_emotion(0.1), _make_manipulation(0.1), _make_links(0.1),
        sender=_make_sender(spf="FAIL", dkim="FAIL", dmarc="FAIL"),
    )
    assert risk.finalScore > baseline.finalScore
    assert risk.scoreReason == "Sender authentication failed (SPF/DKIM/DMARC)"


def test_unknown_sender_auth_adds_little_risk():
    """UNKNOWN SPF/DKIM/DMARC (couldn't verify) must not be treated like a failure."""
    risk = score_email(
        _make_emotion(0.1), _make_manipulation(0.1), _make_links(0.1),
        sender=_make_sender(spf="UNKNOWN", dkim="UNKNOWN", dmarc="UNKNOWN"),
    )
    assert risk.tier == "Low"
    assert risk.scoreReason is None


def test_clean_sender_matches_no_sender_formula():
    """PASS across the board, not typosquatted, and a long-established
    domain (fully verified, nothing suspicious found) must contribute zero
    extra risk. Note: an *unknown* domain age (the default) is NOT the same
    claim — that's tested separately below."""
    risk = score_email(
        _make_emotion(0.9), _make_manipulation(0.9), _make_links(0.9),
        sender=_make_sender(spf="PASS", dkim="PASS", dmarc="PASS", domain_age_days=400),
    )
    expected = min(round((0.9 * 0.35 + 0.9 * 0.30 + 0.9 * 0.20) * 100), 100)
    assert risk.finalScore == expected
    assert risk.tier == "High"
    assert risk.scoreReason is None


def test_young_domain_boosts_score():
    """A domain registered under 30 days ago must raise the score even
    when SPF/DKIM/DMARC all pass — freshly-registered domains are a
    classic phishing indicator independent of DNS record presence."""
    baseline = score_email(
        _make_emotion(0.1), _make_manipulation(0.1), _make_links(0.1),
        sender=_make_sender(spf="PASS", dkim="PASS", dmarc="PASS", domain_age_days=400),
    )
    risk = score_email(
        _make_emotion(0.1), _make_manipulation(0.1), _make_links(0.1),
        sender=_make_sender(spf="PASS", dkim="PASS", dmarc="PASS", domain_age_days=5),
    )
    assert risk.finalScore > baseline.finalScore


def test_unavailable_domain_age_is_not_treated_as_suspicious():
    """A WHOIS lookup that failed/returned nothing (None) must weigh the
    same as an UNKNOWN SPF/DKIM/DMARC result — weak evidence, not proof —
    and must score no worse than a fully UNKNOWN sender overall."""
    unavailable = score_email(
        _make_emotion(0.1), _make_manipulation(0.1), _make_links(0.1),
        sender=_make_sender(spf="UNKNOWN", dkim="UNKNOWN", dmarc="UNKNOWN", domain_age_days=None),
    )
    assert unavailable.tier == "Low"
    assert unavailable.scoreReason is None


def test_no_sender_no_extra_risk():
    """When no sender is provided at all, low scores stay LOW with no scoreReason."""
    risk = score_email(_make_emotion(0.1), _make_manipulation(0.1), _make_links(0.1))
    assert risk.tier == "Low"
    assert risk.finalScore < 40
    assert risk.scoreReason is None
