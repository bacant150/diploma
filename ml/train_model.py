
from __future__ import annotations

from pathlib import Path
import json
import joblib

from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline

try:
    from .text_utils import normalize_text
except ImportError:
    from text_utils import normalize_text


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "dataset.jsonl"
MODEL_PATH = BASE_DIR / "model.joblib"


def load_dataset(path: Path):
    texts = []
    labels = []

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            text = normalize_text(str(item["text"]))
            label = str(item["label"])
            if text:
                texts.append(text)
                labels.append(label)
            else:
                print(f"[WARN] Empty normalized text at line {line_no}")

    return texts, labels


def build_model() -> Pipeline:
    features = FeatureUnion([
        (
            "word_tfidf",
            TfidfVectorizer(
                lowercase=False,
                analyzer="word",
                ngram_range=(1, 3),
                min_df=1,
                max_features=12000,
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
                max_features=18000,
                sublinear_tf=True,
                strip_accents="unicode",
            ),
        ),
    ])

    clf = LogisticRegression(
        max_iter=3000,
        class_weight="balanced",
        C=3.0,
        solver="saga",
    )

    return Pipeline([
        ("features", features),
        ("clf", clf),
    ])


def main():
    print(f"[INFO] Loading dataset: {DATASET_PATH}")
    texts, labels = load_dataset(DATASET_PATH)

    if not texts:
        raise RuntimeError("Dataset is empty after normalization")

    print(f"[INFO] Samples loaded: {len(texts)}")

    X_train, X_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels,
    )

    print("[INFO] Training hybrid TF-IDF + LogisticRegression model...")
    model = build_model()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print(f"Accuracy: {acc:.4f}")
    print("\nClassification report:")
    print(classification_report(y_test, y_pred))

    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
