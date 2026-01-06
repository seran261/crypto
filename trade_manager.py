# trade_manager.py
# ---------------------------------
# Trailing SL after TP1
# ---------------------------------

ACTIVE_TRADES = {}


def register_trade(trade_id, entry, sl, side):
    ACTIVE_TRADES[trade_id] = {
        "entry": entry,
        "sl": sl,
        "side": side,
        "tp1_hit": False
    }


def update_trailing_sl(trade_id, price):
    trade = ACTIVE_TRADES.get(trade_id)
    if not trade:
        return None

    entry = trade["entry"]
    side = trade["side"]

    if not trade["tp1_hit"]:
        return None

    if side == "BUY":
        new_sl = max(trade["sl"], entry * 1.001)
    else:
        new_sl = min(trade["sl"], entry * 0.999)

    trade["sl"] = new_sl
    return round(new_sl, 4)


def mark_tp1_hit(trade_id):
    if trade_id in ACTIVE_TRADES:
        ACTIVE_TRADES[trade_id]["tp1_hit"] = True
