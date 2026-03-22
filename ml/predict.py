from pathlib import Path
import joblib


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.joblib"

_model = None


def load_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def predict_purpose(text: str) -> dict:
    model = load_model()

    cleaned_text = text.strip()
    if not cleaned_text:
        return {
            "purpose": predicted_label,
            "confidence": round(float(confidence), 4) if confidence is not None else None,
        }

    predicted_label = str(model.predict([cleaned_text])[0])

    confidence = None
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba([cleaned_text])[0]
        confidence = float(max(probs))

    return {
        "purpose": predicted_label,
        "confidence": round(confidence, 4) if confidence is not None else None,
    }


if __name__ == "__main__":
    test_queries = [
        "хочу комп для cs2 і valorant",
        "потрібен комп для word excel і браузера",
        "пк для навчання zoom і python",
        "комп'ютер для blender і premiere pro",
    ]

    for query in test_queries:
        result = predict_purpose(query)
        print(query, "->", result)