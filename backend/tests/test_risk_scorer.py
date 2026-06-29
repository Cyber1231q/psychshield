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
    TriggerScores,
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
    risk = score_email(_make_emotion(0.8), _make_manipulation(0.8), _make_links(0.8))
    expected = min(round((0.8 * 0.40 + 0.8 * 0.35 + 0.8 * 0.25) * 100), 100)
    assert risk.finalScore == expected


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


def test_weighted_formula_string():
    risk = score_email(_make_emotion(0.5), _make_manipulation(0.5), _make_links(0.5))
    assert "0.40" in risk.weightedFormula
    assert "0.35" in risk.weightedFormula
    assert "0.25" in risk.weightedFormula


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
