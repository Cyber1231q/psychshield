"""Manipulation detector — identifies psychological manipulation techniques.

Uses regex pattern matching to detect 9 categories of manipulation:
urgency, authority, scarcity, social proof, reciprocity, fear,
commitment, familiarity, and call-to-action urgency.
Each category carries an evidence-strength weight.
"""

import re

from models.schemas import ManipulationResult, ManipulationTechnique

PATTERNS: list[tuple[str, str, float]] = [
    ("Artificial time pressure",
     r"urgent|immediately|within \d+ hours?|expires|deadline|act now|time is running"
     r"|before it.s too late|limited time|respond promptly"
     r"|before close of business|end of.{0,5}day|by.{0,5}today|right away",
     1.2),
    ("Threat of loss",
     r"suspend|terminat|cancel|block|permanent|lose access|penalty|consequences"
     r"|account will be closed|access will be removed|will be disabled"
     r"|will be restricted|will be locked|will be frozen",
     1.3),
    ("Authority impersonation",
     r"IT department|help desk|CEO|director|official notice|security team|bank|government"
     r"|system administrator|compliance officer|fraud department"
     r"|executive director|vice chancellor|managing director|board of directors"
     r"|chief.{0,10}officer|vice president|head of department",
     1.2),
    ("Social proof manipulation",
     r"everyone has|your colleagues|most users|others have already|join thousands",
     1.0),
    ("Scarcity and exclusivity",
     r"only you|selected users|limited offer|exclusive access|you have been chosen",
     1.0),
    ("Reciprocity exploitation",
     r"we gave you|we provided|as a courtesy|in return for|you owe",
     0.9),
    ("Commitment trap",
     r"you agreed|you signed up|you requested|as per your request|you confirmed",
     0.9),
    ("Familiarity abuse",
     r"your friend|your colleague|someone you know|referred by|a mutual contact",
     1.0),
    ("Call to action urgency",
     r"click immediately|click here immediately|verify now|confirm now|update now"
     r"|login now|reset now|click here now"
     r"|verify your identity|verify your account|confirm your identity"
     r"|confirm your account|update your information|confirm your details"
     r"|click the link|click here|click below|click the button"
     r"|open the link|follow the link|tap here|accept the offer"
     r"|process this immediately|confirm once.{0,15}complete",
     1.3),
    ("Suspicious activity alert",
     r"unusual sign.in|unusual activity|suspicious activity|unauthorized access"
     r"|unrecognized device|we detected|we noticed|someone accessed your"
     r"|security alert|if this wasn.t you",
     1.1),
    ("Confidentiality coercion",
     r"do not discuss|don.t tell|keep this between|confidential"
     r"|do not share|don.t share|tell no one|between us"
     r"|do not reply to this|do not forward"
     r"|do not discuss this with anyone|keep this quiet|until.{0,15}finalized"
     r"|don.t mention|this stays between|off the record",
     1.3),
    ("Financial urgency",
     r"wire transfer|send money|bank details|transfer funds"
     r"|process.{0,10}payment|routing number|account number"
     r"|bank account|provide.{0,15}details|send.{0,10}funds"
     r"|new vendor|payment details|wire to|routing.{0,3}\d{5,}",
     1.2),
    ("Unavailability pressure",
     r"cannot take calls|can.t take calls|in a.{0,10}meeting"
     r"|cannot be reached|can.t talk right now|on a flight"
     r"|traveling|out of office|do not call|don.t call me"
     r"|i.m in a meeting|currently unavailable|no time to explain",
     1.2),
    ("Prize and lottery scam",
     r"you have won|you.ve won|congratulations.*winner|lucky winner"
     r"|claim your prize|claim your reward|lottery|sweepstake"
     r"|cash prize|randomly selected|winning notification"
     r"|unclaimed funds|inheritance.*claim|you are a winner"
     r"|million.{0,5}(USD|dollars|pounds|euros|naira)"
     r"|grant has been approved|awarded a grant",
     1.4),
]

SCORE_MAP: dict[int, float] = {
    0: 0.00,
    1: 0.25,
    2: 0.50,
    3: 0.70,
    4: 0.82,
    5: 0.90,
    6: 0.94,
    7: 0.96,
    8: 0.98,
    9: 0.99,
    10: 0.995,
    11: 0.998,
    12: 0.999,
    13: 0.999,
    14: 1.00,
}

_MAX_WEIGHT: float = sum(w for _, _, w in PATTERNS)


def detect_patterns(text: str) -> ManipulationResult:
    """Scan text for psychological manipulation patterns.

    Args:
        text: The email body to analyze.

    Returns:
        ManipulationResult with detected techniques and a weighted
        pattern score using non-linear calibration.
    """
    detected: list[ManipulationTechnique] = []
    total_weight: float = 0.0

    for name, pattern, weight in PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            detected.append(
                ManipulationTechnique(
                    name=name,
                    evidence=f'"{match.group(0)}"',
                )
            )
            total_weight += weight

    count = len(detected)
    base_score = SCORE_MAP.get(count, min(0.5 + count * 0.08, 1.0))

    weight_ratio = total_weight / _MAX_WEIGHT if _MAX_WEIGHT > 0 else 0
    weighted_score = base_score * 0.7 + weight_ratio * 0.3

    detected_names = {t.name for t in detected}
    bec_indicators = {"Confidentiality coercion", "Financial urgency"}
    if bec_indicators.issubset(detected_names):
        weighted_score = min(weighted_score * 1.25, 1.0)

    pattern_score = min(round(weighted_score, 3), 1.0)

    return ManipulationResult(
        model="Regex + Weighted Pattern Matching",
        patternScore=pattern_score,
        techniques=detected,
    )
