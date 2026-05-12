from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import joblib

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline

try:
    from .model_metadata import MODEL_FILENAME, MODEL_VERSION
except ImportError:
    from model_metadata import MODEL_FILENAME, MODEL_VERSION

try:
    from .text_utils import normalize_text
except ImportError:
    from text_utils import normalize_text


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset.jsonl"
MODEL_PATH = BASE_DIR / MODEL_FILENAME
RANDOM_STATE = 42

# Обмеження кількості ознак зменшує ризик перенавчання на малому датасеті.
WORD_MAX_FEATURES = 5_000
CHAR_MAX_FEATURES = 8_000


def load_dataset(path: Path):
    texts: list[str] = []
    labels: list[str] = []
    seen: set[tuple[str, str]] = set()
    skipped_duplicates = 0

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            text = normalize_text(str(item["text"]))
            label = str(item["label"])
            if not text:
                print(f"[WARN] Empty normalized text at line {line_no}")
                continue

            key = (text, label)
            if key in seen:
                skipped_duplicates += 1
                continue

            seen.add(key)
            texts.append(text)
            labels.append(label)

    if skipped_duplicates:
        print(f"[INFO] Skipped duplicate normalized samples: {skipped_duplicates}")

    return texts, labels


def print_class_distribution(labels: list[str]) -> None:
    total = len(labels)
    counts = Counter(labels)
    print("[INFO] Class distribution:")
    for label, count in sorted(counts.items()):
        percent = 100 * count / total if total else 0
        print(f"  - {label}: {count} samples ({percent:.1f}%)")


def build_model() -> Pipeline:
    features = FeatureUnion([
        (
            "word_tfidf",
            TfidfVectorizer(
                lowercase=False,
                analyzer="word",
                ngram_range=(1, 2),
                min_df=1,
                max_features=WORD_MAX_FEATURES,
                sublinear_tf=True,
                strip_accents="unicode",
            ),
        ),
        (
            "char_tfidf",
            TfidfVectorizer(
                lowercase=False,
                analyzer="char_wb",
                ngram_range=(3, 5),
                min_df=1,
                max_features=CHAR_MAX_FEATURES,
                sublinear_tf=True,
                strip_accents="unicode",
            ),
        ),
    ])

    clf = LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        C=1.0,
        solver="saga",
        random_state=RANDOM_STATE,
    )

    return Pipeline([
        ("features", features),
        ("clf", clf),
    ])


def cross_validate_model(texts: list[str], labels: list[str]) -> tuple[float, float]:
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_val_score(build_model(), texts, labels, cv=cv, scoring="accuracy")
    return float(scores.mean()), float(scores.std())


def main():
    print(f"[INFO] Loading dataset: {DATASET_PATH}")
    texts, labels = load_dataset(DATASET_PATH)

    if not texts:
        raise RuntimeError("Dataset is empty after normalization")

    print(f"[INFO] Samples loaded after deduplication: {len(texts)}")
    print_class_distribution(labels)

    print("[INFO] Running 5-fold cross-validation...")
    cv_mean, cv_std = cross_validate_model(texts, labels)
    print(f"5-fold CV accuracy: {cv_mean:.4f} ± {cv_std:.4f}")

    X_train, X_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=labels,
    )

    print("[INFO] Training hybrid TF-IDF + LogisticRegression model...")
    model = build_model()
    model.fit(X_train, y_train)
    model.model_version = MODEL_VERSION
    model.training_samples = len(X_train)
    model.evaluation = {
        "cv_accuracy_mean": round(cv_mean, 4),
        "cv_accuracy_std": round(cv_std, 4),
        "word_max_features": WORD_MAX_FEATURES,
        "char_max_features": CHAR_MAX_FEATURES,
    }

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print(f"Hold-out accuracy: {acc:.4f}")
    print("\nClassification report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    joblib.dump(model, MODEL_PATH)
    print(f"\nModel version: {MODEL_VERSION}")
    print(f"Model saved to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
