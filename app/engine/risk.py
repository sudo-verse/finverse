def risk_management(price):
    stop_loss = price * 0.98
    target = price * 1.04
    return stop_loss, target