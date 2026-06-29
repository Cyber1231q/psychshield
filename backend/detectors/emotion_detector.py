"""Emotion detector — identifies emotional manipulation cues in email text.

Uses an ensemble of TF-IDF + LinearSVC (GoEmotions) and keyword scoring
when the ML model is available. Falls back to keywords-only otherwise.
The ensemble takes max(ml, keyword) per trigger so domain-specific
phishing vocabulary boosts the ML model's conservative estimates.
"""

import os

import joblib
import numpy as np

from models.schemas import EmotionCategoryScore, EmotionDetectionResult

TRIGGERS: list[str] = ["urgency", "fear", "authority", "trust", "pity"]

# ── ML model state (lazy-loaded at module startup) ──────────────

_vectorizer = None
_models = None
_using_ml: bool = False


def load_emotion_model() -> None:
    """Load trained TF-IDF vectorizer and SVM models from disk."""
    global _vectorizer, _models, _using_ml
    model_path = os.getenv("MODEL_PATH", "./saved_models/")
    vec_path = f"{model_path}emotion_vectorizer.joblib"
    mdl_path = f"{model_path}emotion_models.joblib"
    if os.path.exists(vec_path) and os.path.exists(mdl_path):
        _vectorizer = joblib.load(vec_path)
        _models = joblib.load(mdl_path)
        _using_ml = True
        print("Emotion model loaded from disk (ML mode)")
    else:
        print("No saved model found — using keyword fallback")


load_emotion_model()

# ── Single-word trigger lists ───────────────────────────────────

URGENCY_WORDS: list[str] = [
    "urgent", "immediately", "asap", "now", "hurry",
    "deadline", "expires", "critical", "emergency", "instant",
    "overdue", "promptly", "expiring",
]
FEAR_WORDS: list[str] = [
    "suspended", "terminated", "blocked", "threat", "danger",
    "warning", "risk", "breach", "compromised", "attack", "penalty",
    "locked", "frozen", "unauthorized", "restricted",
    "disabled", "violated", "revoked",
]
AUTHORITY_WORDS: list[str] = [
    "official", "department", "management", "director",
    "required", "mandatory", "compliance", "policy", "headquarters",
    "administrator", "regulation",
]
TRUST_WORDS: list[str] = [
    "verified", "secure", "trusted", "confirmed", "legitimate",
    "certified", "approved", "authorized", "genuine",
    "protected", "encrypted",
    "congratulations", "winner", "awarded", "selected",
]
PITY_WORDS: list[str] = [
    "help", "please", "desperate", "struggling", "charity",
    "kindness", "assistance", "support", "unfortunate", "sorry",
    "humanitarian", "orphan",
]

# ── Phrase-level triggers (catches subtle/indirect phishing) ────

URGENCY_PHRASES: list[str] = [
    "within 24 hours", "within 48 hours",
    "time sensitive", "limited time",
    "act now", "respond immediately",
    "failure to respond", "if you do not respond",
    "your account will be", "will be permanently",
    "before it is too late", "don't delay",
    "at your earliest", "as soon as possible",
    "will expire", "action required",
    "must be completed", "respond promptly",
    "accept the offer", "click the link",
    "offer expires", "position will be filled",
]
FEAR_PHRASES: list[str] = [
    "suspicious activity", "unusual sign-in",
    "unusual activity", "unrecognized device",
    "someone accessed your", "unauthorized access",
    "security alert", "security notice",
    "we detected", "we noticed",
    "failed verification", "identity could not be verified",
    "account will be closed", "account will be disabled",
    "account has been limited", "access will be removed",
    "may be compromised", "has been flagged",
    "if this wasn't you", "if this was not you",
]
AUTHORITY_PHRASES: list[str] = [
    "IT department", "security team",
    "system administrator", "your administrator",
    "as per our policy", "in accordance with",
    "regulatory requirement", "company policy requires",
    "we require you to", "you are required to",
    "account review", "annual verification",
    "routine security check", "identity verification required",
    "on behalf of", "from the office of",
]
TRUST_PHRASES: list[str] = [
    "for your security", "for your protection",
    "to protect your account", "to secure your account",
    "verify your identity", "confirm your details",
    "update your information", "update your records",
    "confirm your account", "verify your account",
    "we value your security", "your safety matters",
    "trusted source", "secure connection",
    "keep your account safe", "ensure your security",
    "you have won", "you have been selected",
    "claim your prize", "claim your reward",
    "cash prize", "lucky winner", "randomly selected",
    "grant has been approved", "inheritance claim",
]
PITY_PHRASES: list[str] = [
    "in need of", "lost everything",
    "medical emergency", "late husband",
    "charitable cause", "on behalf of the family",
    "your generous", "count on your",
    "only you can help", "no one else to turn to",
    "dying wish", "leave the funds to you",
]


# ── Public API ──────────────────────────────────────────────────

def detect_emotions(text: str) -> EmotionDetectionResult:
    """Analyze emotional content in the given text.

    Uses the trained ML model if loaded, otherwise falls back
    to keyword-based scoring.

    Args:
        text: The email body to analyze.

    Returns:
        EmotionDetectionResult with per-category scores and a composite
        emotion score.
    """
    if _using_ml and _vectorizer and _models:
        return _detect_emotions_ml(text)
    return _detect_emotions_keywords(text)


def train_emotion_model() -> None:
    """Stub pointing to the standalone training script."""
    print("Run 'python train_emotion_model.py' from the backend directory")
    print("to train the GoEmotions TF-IDF + LinearSVC model.")


# ── Ensemble detection (ML + keywords) ─────────────────────────

WORD_TRIGGER_MAP: dict[str, list[str]] = {
    "urgency": URGENCY_WORDS,
    "fear": FEAR_WORDS,
    "authority": AUTHORITY_WORDS,
    "trust": TRUST_WORDS,
    "pity": PITY_WORDS,
}

PHRASE_TRIGGER_MAP: dict[str, list[str]] = {
    "urgency": URGENCY_PHRASES,
    "fear": FEAR_PHRASES,
    "authority": AUTHORITY_PHRASES,
    "trust": TRUST_PHRASES,
    "pity": PITY_PHRASES,
}


def _detect_emotions_ml(text: str) -> EmotionDetectionResult:
    """Ensemble scoring: max(ML sigmoid, word score, phrase score) per trigger.

    Args:
        text: The email body to analyze.

    Returns:
        EmotionDetectionResult from the ensemble pipeline.
    """
    X = _vectorizer.transform([text])
    scores: dict[str, float] = {}
    for trigger in TRIGGERS:
        clf = _models[trigger]
        decision = clf.decision_function(X)[0]
        ml_score = float(1 / (1 + np.exp(-decision)))
        kw_score = _score_words(text, WORD_TRIGGER_MAP[trigger])
        ph_score = _score_phrases(text, PHRASE_TRIGGER_MAP[trigger])
        scores[trigger] = round(min(max(ml_score, kw_score, ph_score), 1.0), 3)

    emotion_score = (
        scores["urgency"] * 0.25
        + scores["fear"] * 0.25
        + scores["authority"] * 0.20
        + scores["trust"] * 0.15
        + scores["pity"] * 0.10
    )

    category_scores = [
        EmotionCategoryScore(category=t, score=scores[t])
        for t in TRIGGERS
    ]
    highest = max(category_scores, key=lambda x: x.score)
    summary = (
        f"Ensemble model active. "
        f"Dominant trigger: {highest.category} ({highest.score:.0%})."
    )

    return EmotionDetectionResult(
        model="TF-IDF + LinearSVC + Keywords (Ensemble)",
        categoryScores=category_scores,
        emotionScore=round(emotion_score, 3),
        summary=summary,
    )


# ── Scoring helpers ─────────────────────────────────────────────

def _score_words(text: str, words: list[str]) -> float:
    """Score how many single-word triggers appear in the text.

    Args:
        text: The email body to analyze.
        words: List of trigger words for this category.

    Returns:
        A score between 0.0 and 1.0.
    """
    text_lower = text.lower()
    matches = sum(1 for w in words if w in text_lower)
    return min(matches / max(len(words) * 0.2, 1), 1.0)


def _score_phrases(text: str, phrases: list[str]) -> float:
    """Score how many multi-word phrases appear in the text.

    Phrases catch subtle phishing that uses indirect language
    like 'for your security' or 'unusual sign-in detected'.

    Args:
        text: The email body to analyze.
        phrases: List of trigger phrases for this category.

    Returns:
        A score between 0.0 and 1.0.
    """
    text_lower = text.lower()
    matches = sum(1 for p in phrases if p in text_lower)
    return min(matches / max(len(phrases) * 0.15, 1), 1.0)


def _combined_trigger_score(text: str, trigger: str) -> float:
    """Compute max(word_score, phrase_score) for a trigger category."""
    w = _score_words(text, WORD_TRIGGER_MAP[trigger])
    p = _score_phrases(text, PHRASE_TRIGGER_MAP[trigger])
    return max(w, p)


# ── Keyword + phrase fallback ──────────────────────────────────

def _detect_emotions_keywords(text: str) -> EmotionDetectionResult:
    """Keyword and phrase-based emotion detection fallback.

    Args:
        text: The email body to analyze.

    Returns:
        EmotionDetectionResult from word + phrase matching.
    """
    scores: dict[str, float] = {}
    for trigger in TRIGGERS:
        scores[trigger] = _combined_trigger_score(text, trigger)

    emotion_score = (
        scores["urgency"] * 0.25
        + scores["fear"] * 0.25
        + scores["authority"] * 0.20
        + scores["trust"] * 0.15
        + scores["pity"] * 0.10
    )

    category_scores = [
        EmotionCategoryScore(category=t, score=round(scores[t], 3))
        for t in TRIGGERS
    ]

    highest = max(category_scores, key=lambda x: x.score)
    summary = f"Dominant trigger: {highest.category} ({highest.score:.0%}). "
    if emotion_score > 0.6:
        summary += "High psychological manipulation indicators detected."
    elif emotion_score > 0.3:
        summary += "Moderate emotional manipulation indicators present."
    else:
        summary += "Low emotional manipulation indicators."

    return EmotionDetectionResult(
        model="Keyword + Phrase Scoring v2",
        categoryScores=category_scores,
        emotionScore=round(emotion_score, 3),
        summary=summary,
    )
