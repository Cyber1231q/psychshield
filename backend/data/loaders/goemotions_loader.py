"""GoEmotions loader — maps 28 GoEmotions labels to 5 PsychShield triggers.

Downloads the Google GoEmotions dataset from HuggingFace and produces
DataFrames with binary columns for each trigger category.
"""

from typing import Any

import pandas as pd
from datasets import load_dataset

EMOTION_TO_TRIGGER: dict[int, str] = {
    0:  "admiration",     # -> authority
    1:  "amusement",      # -> neutral
    2:  "anger",          # -> fear
    3:  "annoyance",      # -> fear
    4:  "approval",       # -> authority
    5:  "caring",         # -> trust
    6:  "confusion",      # -> neutral
    7:  "curiosity",      # -> neutral
    8:  "desire",         # -> urgency
    9:  "disappointment", # -> pity
    10: "disapproval",    # -> fear
    11: "disgust",        # -> fear
    12: "embarrassment",  # -> pity
    13: "excitement",     # -> urgency
    14: "fear",           # -> fear
    15: "gratitude",      # -> authority
    16: "grief",          # -> pity
    17: "joy",            # -> trust
    18: "love",           # -> trust
    19: "nervousness",    # -> urgency
    20: "optimism",       # -> trust
    21: "pride",          # -> authority
    22: "realization",    # -> neutral
    23: "relief",         # -> trust
    24: "remorse",        # -> pity
    25: "sadness",        # -> pity
    26: "surprise",       # -> neutral
    27: "neutral",        # -> neutral
}

TRIGGER_MAP: dict[str, list[int]] = {
    "urgency":   [8, 13, 19],
    "fear":      [2, 3, 10, 11, 14],
    "authority": [0, 4, 15, 21],
    "trust":     [5, 17, 18, 20, 23],
    "pity":      [9, 12, 16, 24, 25],
}


def load_goemotions() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load GoEmotions and return train/test DataFrames with trigger columns.

    Returns:
        Tuple of (train_df, test_df) each with columns:
        text, urgency, fear, authority, trust, pity (binary 0/1).
    """
    print("Loading GoEmotions dataset...")
    ds = load_dataset("google-research-datasets/go_emotions", "simplified")

    def process_split(split: Any) -> pd.DataFrame:
        rows: list[dict[str, Any]] = []
        for item in split:
            text = item["text"]
            labels = item["labels"]
            row: dict[str, Any] = {"text": text}
            for trigger, emotion_ids in TRIGGER_MAP.items():
                row[trigger] = 1 if any(l in emotion_ids for l in labels) else 0
            rows.append(row)
        return pd.DataFrame(rows)

    train_df = process_split(ds["train"])
    test_df = process_split(ds["test"])
    print(f"Train: {len(train_df)} samples, Test: {len(test_df)} samples")
    return train_df, test_df


def get_goemotions_stats() -> dict[str, Any]:
    """Return summary statistics about the GoEmotions dataset.

    Returns:
        Dict with train_size, test_size, and trigger names.
    """
    train_df, test_df = load_goemotions()
    return {
        "train_size": len(train_df),
        "test_size": len(test_df),
        "triggers": list(TRIGGER_MAP.keys()),
    }
