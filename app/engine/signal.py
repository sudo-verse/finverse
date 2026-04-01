def generate_signal(label, score, event):
    if score < 0.75:
        return "HOLD"

    if event == "EARNINGS":
        if label == "positive":
            return "STRONG BUY"
        elif label == "negative":
            return "STRONG SELL"

    if event == "POLICY":
        if label == "negative":
            return "SELL"

    if label == "positive":
        return "BUY"
    elif label == "negative":
        return "SELL"

    return "HOLD"
def keyword_signal(text):
    text = text.lower()

    score = 0
    signals = []

    # High impact
    for k, (signal, weight) in HIGH_IMPACT.items():
        if k in text:
            score += weight
            signals.append((k, signal))

    # Medium impact
    for k, (signal, weight) in MEDIUM_IMPACT.items():
        if k in text:
            score += weight
            signals.append((k, signal))

    # Final decision
    if score >= 3:
        return "STRONG BUY", score, signals
    elif score <= -3:
        return "STRONG SELL", score, signals
    elif score > 0:
        return "BUY", score, signals
    elif score < 0:
        return "SELL", score, signals

    return "HOLD", score, signals