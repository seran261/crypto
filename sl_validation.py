# sl_validation.py
# ---------------------------------
# Symbol-based Stop Loss validation
# ---------------------------------

SYMBOL_SL_RULES = {
    "BTC": 0.0020,   # 0.20%
    "ETH": 0.0025,   # 0.25%
    "BNB": 0.0030,
    "SOL": 0.0035,
    "XRP": 0.0040,
    "LINK": 0.0035,
    "LTC": 0.0035,
    "AVAX": 0.0040,
    "AAVE": 0.0045,
}

DEFAULT_MIN_SL = 0.0050  # 0.50% fallback


def get_min_sl_pct(symbol):
    symbol = symbol.upper()
    for key in SYMBOL_SL_RULES:
        if symbol.startswith(key):
            return SYMBOL_SL_RULES[key]
    return DEFAULT_MIN_SL


def validate_sl(entry, sl, side, symbol):
    min_pct = get_min_sl_pct(symbol)

    if side == "BUY":
        min_sl = entry * (1 - min_pct)
        if sl > min_sl:
            sl = min_sl

    elif side == "SELL":
        min_sl = entry * (1 + min_pct)
        if sl < min_sl:
            sl = min_sl

    return round(sl, 4)
