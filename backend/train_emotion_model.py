"""PsychShield emotion model training script.

Trains one LinearSVC per trigger category using TF-IDF features
from the GoEmotions dataset. Run once, then the emotion detector
loads the saved models automatically.

Usage:
    cd backend && python train_emotion_model.py
"""

import json
import os
import sys
from datetime import datetime

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score
from sklearn.svm import LinearSVC

sys.path.insert(0, ".")
from data.loaders.goemotions_loader import load_goemotions

TRIGGERS: list[str] = ["urgency", "fear", "authority", "trust", "pity"]
MODEL_PATH: str = os.getenv("MODEL_PATH", "./saved_models/")
os.makedirs(MODEL_PATH, exist_ok=True)


def train() -> dict[str, float]:
    """Train TF-IDF + LinearSVC models for each trigger and save to disk.

    Returns:
        Dict mapping trigger name to accuracy percentage.
    """
    print("=" * 50)
    print("PsychShield Emotion Model Training")
    print("=" * 50)

    print("\nLoading GoEmotions dataset...")
    train_df, test_df = load_goemotions()

    print("\nBuilding TF-IDF vectorizer...")
    vectorizer = TfidfVectorizer(
        max_features=15000,
        ngram_range=(1, 2),
        sublinear_tf=True,
        strip_accents="unicode",
        analyzer="word",
        token_pattern=r"\w{2,}",
        min_df=2,
    )
    X_train = vectorizer.fit_transform(train_df["text"])
    X_test = vectorizer.transform(test_df["text"])

    models: dict[str, LinearSVC] = {}
    results: dict[str, float] = {}
    print("\nTraining SVM classifier for each trigger:")

    for trigger in TRIGGERS:
        print(f"  Training {trigger}...", end=" ")
        y_train = train_df[trigger].values
        y_test = test_df[trigger].values

        clf = LinearSVC(C=1.0, max_iter=2000)
        clf.fit(X_train, y_train)
        y_pred = clf.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        models[trigger] = clf
        results[trigger] = round(acc * 100, 2)
        print(f"accuracy = {acc:.1%}")

    overall = sum(results.values()) / len(results)
    print(f"\nOverall average accuracy: {overall:.1f}%")

    print("\nSaving models...")
    joblib.dump(vectorizer, f"{MODEL_PATH}emotion_vectorizer.joblib")
    joblib.dump(models, f"{MODEL_PATH}emotion_models.joblib")

    metadata = {
        "trained_at": datetime.now().isoformat(),
        "accuracy_per_trigger": results,
        "overall_accuracy": round(overall, 2),
        "vectorizer_features": vectorizer.max_features,
        "model_type": "LinearSVC + TF-IDF",
    }
    with open(f"{MODEL_PATH}emotion_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Models saved to {MODEL_PATH}")
    print("\n=== TRAINING COMPLETE ===")
    print(json.dumps(results, indent=2))
    print(f"Overall: {overall:.1f}% (target >= 90%)")

    return results


if __name__ == "__main__":
    train()
