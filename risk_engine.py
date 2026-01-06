# risk_engine.py
# -------------------------------------------------
# ATR Scaling + Spread-aware SL
# -------------------------------------------------

def atr_based_sl(entry, atr, side, timeframe):
    """
    1m (HFT) → tighter
    5m (Scalp) → wider
    """
    multiplier = 0.8 if timeframe == "1m" else 1.4
    distance = atr * multiplier

    if side == "BUY":
        return entry - distance
    else:
        return entry + distance


def spread_adjust_sl(sl, spread, side, mode):
    if mode != "HFT":
        return sl

    buffer = spread * 1.5

    if side == "BUY":
        return sl - buffer
    else:
        return sl + buffer
