"""Tests for the manipulation detector module."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from detectors.manipulation_detector import detect_patterns


def test_high_risk_email_detects_techniques():
    result = detect_patterns("URGENT: suspended immediately click now")
    assert len(result.techniques) >= 2


def test_legitimate_email_zero_techniques():
    result = detect_patterns("Hi team, lunch at 1pm today?")
    assert len(result.techniques) == 0


def test_score_between_zero_and_one():
    result = detect_patterns("any text")
    assert 0 <= result.patternScore <= 1


def test_time_pressure_detected():
    result = detect_patterns("You must act now, this expires within 24 hours")
    names = [t.name for t in result.techniques]
    assert "Artificial time pressure" in names


def test_threat_of_loss_detected():
    result = detect_patterns("Your account will be permanently suspended")
    names = [t.name for t in result.techniques]
    assert "Threat of loss" in names


def test_authority_impersonation_detected():
    result = detect_patterns("This is from the IT department help desk")
    names = [t.name for t in result.techniques]
    assert "Authority impersonation" in names


def test_call_to_action_detected():
    result = detect_patterns("Please click immediately to verify now")
    names = [t.name for t in result.techniques]
    assert "Call to action urgency" in names


def test_evidence_is_populated():
    result = detect_patterns("urgent deadline act now")
    for t in result.techniques:
        assert len(t.evidence) > 0


def test_model_field_set():
    result = detect_patterns("anything")
    assert result.model == "Regex + Pattern Matching"


def test_max_score_is_one():
    result = detect_patterns(
        "urgent immediately within 2 hours expires deadline act now "
        "suspended terminated cancel block permanent lose access penalty "
        "IT department help desk CEO director official notice security team "
        "everyone has your colleagues most users others have already "
        "only you selected users limited offer exclusive access "
        "we gave you we provided as a courtesy in return for "
        "you agreed you signed up you requested as per your request "
        "your friend your colleague someone you know referred by "
        "click immediately verify now confirm now update now"
    )
    assert result.patternScore <= 1.0
