def detect_event(text):
    text = text.lower()

    if "earnings" in text or "results" in text:
        return "EARNINGS"
    elif "government" in text or "policy" in text:
        return "POLICY"
    elif "acquire" in text or "merger" in text:
        return "MERGER"
    elif "deal" in text or "contract" in text:
        return "CONTRACT"
    else:
        return "GENERAL"