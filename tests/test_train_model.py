from __future__ import annotations

import json
from pathlib import Path


def test_load_dataset_deduplicates_normalized_samples(tmp_path: Path):
    from ml.train_model import load_dataset

    dataset_path = tmp_path / "dataset.jsonl"
    rows = [
        {"text": "іграти", "label": "gaming"},
        {"text": "іграть", "label": "gaming"},
        {"text": "ПК для офісу", "label": "office"},
    ]
    dataset_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows),
        encoding="utf-8",
    )

    texts, labels = load_dataset(dataset_path)

    assert len(texts) == 2
    assert labels.count("office") == 1
    assert labels.count("gaming") == 1


def test_build_model_uses_limited_feature_space():
    from ml.train_model import CHAR_MAX_FEATURES, WORD_MAX_FEATURES, build_model

    model = build_model()
    features = model.named_steps["features"]
    transformers = dict(features.transformer_list)

    assert WORD_MAX_FEATURES == 5000
    assert CHAR_MAX_FEATURES == 8000
    assert transformers["word_tfidf"].max_features == WORD_MAX_FEATURES
    assert transformers["char_tfidf"].max_features == CHAR_MAX_FEATURES
    assert transformers["word_tfidf"].ngram_range == (1, 2)
