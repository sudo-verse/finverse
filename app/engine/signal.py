def generate_signal(label, score, event):
    if score < 0.8:
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