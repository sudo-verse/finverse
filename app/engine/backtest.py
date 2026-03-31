def evaluate_signal(signal, prev_price, curr_price):
    if prev_price is None or curr_price is None:
        return None

    price_change = curr_price - prev_price

    if signal in ["BUY", "STRONG BUY"]:
        return price_change > 0

    if signal in ["SELL", "STRONG SELL"]:
        return price_change < 0

    return None