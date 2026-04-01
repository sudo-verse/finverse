# app/engine/keyword_engine.py

HIGH_IMPACT = {
    "beat estimates": ("STRONG BUY", 3),
    "record profit": ("STRONG BUY", 3),
    "strong earnings": ("STRONG BUY", 3),
    "order win": ("STRONG BUY", 2),

    "miss estimates": ("STRONG SELL", -3),
    "loss widens": ("STRONG SELL", -3),
    "profit drops": ("STRONG SELL", -3),
    "fraud": ("STRONG SELL", -5),
}

MEDIUM_IMPACT = {
    "rally": ("BUY", 1),
    "surge": ("BUY", 1),
    "growth": ("BUY", 1),

    "decline": ("SELL", -1),
    "fall": ("SELL", -1),
}

def keyword_signal(text):
    text = text.lower()

    score = 0
    matches = []

    for k, (signal, weight) in HIGH_IMPACT.items():
        if k in text:
            score += weight
            matches.append(k)

    for k, (signal, weight) in MEDIUM_IMPACT.items():
        if k in text:
            score += weight
            matches.append(k)

    if score >= 3:
        return "STRONG BUY", score, matches
    elif score <= -3:
        return "STRONG SELL", score, matches
    elif score > 0:
        return "BUY", score, matches
    elif score < 0:
        return "SELL", score, matches

    return "HOLD", score, matches


def final_signal(sentiment_label, sentiment_score, keyword_sig, keyword_score):

    # keyword dominates if strong
    if keyword_sig in ["STRONG BUY", "STRONG SELL"]:
        return keyword_sig

    # combine both
    if sentiment_label == "positive" and keyword_score > 0:
        return "BUY"

    if sentiment_label == "negative" and keyword_score < 0:
        return "SELL"

    return "HOLD"