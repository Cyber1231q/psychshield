"""Tests for the emotion detector module."""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from detectors.emotion_detector import detect_emotions


def test_phishing_email_scores_above_zero():
    result = detect_emotions("URGENT: Your account has been suspended immediately")
    assert result.emotionScore > 0


def test_benign_email_scores_low():
    result = detect_emotions("Hi team, the meeting is at 3pm. See you there.")
    assert result.emotionScore < 0.3


def test_returns_five_categories():
    result = detect_emotions("any text")
    assert len(result.categoryScores) == 5
    names = {s.category for s in result.categoryScores}
    assert names == {"urgency", "fear", "authority", "trust", "pity"}


def test_emotion_score_between_zero_and_one():
    result = detect_emotions("random test email body")
    assert 0 <= result.emotionScore <= 1


def test_category_scores_between_zero_and_one():
    result = detect_emotions("URGENT suspended blocked immediately danger")
    for s in result.categoryScores:
        assert 0 <= s.score <= 1.0, f"{s.category} score {s.score} out of range"


def test_urgency_dominates_for_urgent_email():
    result = detect_emotions("URGENT: act immediately, deadline expires now, hurry!")
    scores = {s.category: s.score for s in result.categoryScores}
    assert scores["urgency"] >= scores["pity"]
    assert scores["urgency"] >= scores["trust"]


def test_fear_dominates_for_threat_email():
    result = detect_emotions("Your account has been suspended, terminated, and blocked due to a breach")
    scores = {s.category: s.score for s in result.categoryScores}
    assert scores["fear"] >= scores["trust"]
    assert scores["fear"] >= scores["pity"]


def test_model_field_is_populated():
    result = detect_emotions("test")
    assert result.model != ""


def test_summary_is_populated():
    result = detect_emotions("URGENT: danger warning")
    assert len(result.summary) > 10


def test_latency_under_one_second():
    start = time.time()
    detect_emotions("URGENT: Your account compromised. Click immediately.")
    elapsed = time.time() - start
    assert elapsed < 1.0, f"Latency {elapsed:.2f}s exceeds 1s"
