from config import (
    SCALP_TP, SCALP_SL,
    HFT_TP, HFT_SL,
    SIGNAL_COOLDOWN, MIN_CONFIDENCE
)

from user_state import get_mode, can_send
from sl_validation import validate_sl
from risk_engine import atr_based_sl, spread_adjust_sl

from data_fetcher import (
    liquidity_sweep,
    htf_support_resistance,
    get_atr,
    get_spread,
    get_orderbook_imbalance,
    detect_orderbook_spoofing,
    get_vwap_bands
)


def confidence_score(volume_spike, sweep):
    score = 20
    if volume_spike:
        score += 40
    if sweep:
        score += 40
    return score


def generate_signal(symbol, price, volume, chat_id):
    mode = get_mode(chat_id)
    volume_spike = volume > 5000

    timeframe = "1m" if mode == "HFT" else "5m"

    sweep = liquidity_sweep(symbol, timeframe)
    support, resistance = htf_support_resistance(symbol)

    atr = get_atr(symbol, timeframe)
    spread = get_spread(symbol)
    imbalance = get_orderbook_imbalance(symbol)
    spoofing = detect_orderbook_spoofing(symbol)
    vwap = get_vwap_bands(symbol, timeframe)

    if spoofing:
        return None

    conf = confidence_score(volume_spike, sweep)

    if conf < MIN_CONFIDENCE:
        return None

    if not can_send(chat_id, symbol, SIGNAL_COOLDOWN):
        return None

    tp_pct, sl_pct = (
        (SCALP_TP, SCALP_SL) if mode == "SCALP"
        else (HFT_TP, HFT_SL)
    )

    # ==========================
    # 🟢 BUY — DISCOUNT ZONE
    # ==========================
    if (
        sweep == "SWEEP_DOWN"
        and imbalance > 1.2
        and price <= vwap["lower_1"]
    ):
        entry = price
        tp = entry * (1 + tp_pct)

        sl = max(
            entry * (1 - sl_pct),
            atr_based_sl(entry, atr, "BUY", timeframe)
        )

        if support and support < entry:
            sl = max(sl, support * 0.995)

        sl = spread_adjust_sl(sl, spread, "BUY", mode)
        sl = validate_sl(entry, sl, "BUY", symbol)

        return {
            "symbol": symbol,
            "side": "BUY",
            "mode": mode,
            "confidence": conf,
            "entry": round(entry, 4),
            "tp": round(tp, 4),
            "sl": sl
        }

    # ==========================
    # 🔴 SELL — PREMIUM ZONE
    # ==========================
    if (
        sweep == "SWEEP_UP"
        and imbalance < 0.8
        and price >= vwap["upper_1"]
    ):
        entry = price
        tp = entry * (1 - tp_pct)

        sl = min(
            entry * (1 + sl_pct),
            atr_based_sl(entry, atr, "SELL", timeframe)
        )

        if resistance and resistance > entry:
            sl = min(sl, resistance * 1.005)

        sl = spread_adjust_sl(sl, spread, "SELL", mode)
        sl = validate_sl(entry, sl, "SELL", symbol)

        return {
            "symbol": symbol,
            "side": "SELL",
            "mode": mode,
            "confidence": conf,
            "entry": round(entry, 4),
            "tp": round(tp, 4),
            "sl": sl
        }

    return None
