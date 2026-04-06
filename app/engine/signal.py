GOOD_EVENTS = ["order_win","agreement_mou","earnings","securities_issuance"]
MIN_SCORE = 0.75

def generate_signal(label, score, event):
    if event in GOOD_EVENTS and label == "positive" and score > MIN_SCORE:
        return "BUY"
    return "HOLD"   
