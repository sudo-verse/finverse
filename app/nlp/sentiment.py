_model = None


def _get_model():
    """Load FinBERT on first use, not at import time — the model weighs
    hundreds of MB and importing this module must stay cheap (the API
    backend imports the engine but may never run it)."""
    global _model
    if _model is None:
        from transformers import pipeline

        _model = pipeline("sentiment-analysis", model="ProsusAI/finbert")
    return _model


def get_sentiment(text):
    result = _get_model()(text)[0]
    return result["label"], result["score"]
