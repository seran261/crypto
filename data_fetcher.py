# data_fetcher.py
# -------------------------------------------------
# OKX Market Data
# LTF Price + Volume + Liquidity + VWAP σ
# -------------------------------------------------

import time
import ccxt
import numpy as np
from collections import deque

exchange = ccxt.okx({
    "enableRateLimit": True,
    "options": {"defaultType": "swap"}
})

PRICE_CACHE = {}
ATR_CACHE = {}
SPREAD_CACHE = {}
VWAP_CACHE = {}
ORDERBOOK_HISTORY = {}

PRICE_TTL = 2
ATR_TTL = 60
SPREAD_TTL = 5
VWAP_TTL = 10

SPOOF_WINDOW = 5
SPOOF_THRESHOLD = 0.4


def _now():
    return int(time.time())


# -------------------------------------------------
# LTF PRICE + VOLUME (FIXED)
# -------------------------------------------------
def fetch_ltf_price(symbol):
    now = _now()

    if symbol in PRICE_CACHE and now - PRICE_CACHE[symbol]["ts"] < PRICE_TTL:
        cached = PRICE_CACHE[symbol]
        return cached["price"], cached["volume"]

    try:
        ticker = exchange.fetch_ticker(symbol)

        price = float(ticker["last"])
        volume = float(ticker.get("baseVolume", 0))

        PRICE_CACHE[symbol] = {
            "price": price,
            "volume": volume,
            "ts": now
        }

        return price, volume

    except Exception:
        return None, None


# -------------------------------------------------
# REAL LIQUIDITY SWEEP
# -------------------------------------------------
def liquidity_sweep(symbol, timeframe="1m", lookback=20):
    try:
        candles = exchange.fetch_ohlcv(symbol, timeframe, limit=lookback)
        highs = [c[2] for c in candles[:-1]]
        lows = [c[3] for c in candles[:-1]]

        last = candles[-1]
        last_high, last_low, last_close = last[2], last[3], last[4]

        eq_high = max(highs)
        eq_low = min(lows)

        if last_low < eq_low and last_close > eq_low:
            return "SWEEP_DOWN"

        if last_high > eq_high and last_close < eq_high:
            return "SWEEP_UP"

        return None
    except Exception:
        return None


# -------------------------------------------------
# ATR
# -------------------------------------------------
def get_atr(symbol, timeframe="1m", period=14):
    key = f"{symbol}_{timeframe}"
    now = _now()

    if key in ATR_CACHE and now - ATR_CACHE[key]["ts"] < ATR_TTL:
        return ATR_CACHE[key]["value"]

    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=period + 1)
        highs = np.array([c[2] for c in ohlcv])
        lows = np.array([c[3] for c in ohlcv])
        closes = np.array([c[4] for c in ohlcv])

        tr = np.maximum(
            highs[1:] - lows[1:],
            np.maximum(abs(highs[1:] - closes[:-1]), abs(lows[1:] - closes[:-1]))
        )

        atr = float(np.mean(tr))
        ATR_CACHE[key] = {"value": atr, "ts": now}
        return atr
    except Exception:
        return 0


# -------------------------------------------------
# SPREAD
# -------------------------------------------------
def get_spread(symbol):
    now = _now()

    if symbol in SPREAD_CACHE and now - SPREAD_CACHE[symbol]["ts"] < SPREAD_TTL:
        return SPREAD_CACHE[symbol]["value"]

    try:
        ob = exchange.fetch_order_book(symbol, limit=5)
        spread = ob["asks"][0][0] - ob["bids"][0][0]
        SPREAD_CACHE[symbol] = {"value": spread, "ts": now}
        return spread
    except Exception:
        return 0


# -------------------------------------------------
# ORDERBOOK IMBALANCE
# -------------------------------------------------
def get_orderbook_imbalance(symbol, depth=10):
    try:
        ob = exchange.fetch_order_book(symbol, limit=depth)
        bid_vol = sum(b[1] for b in ob["bids"])
        ask_vol = sum(a[1] for a in ob["asks"])
        return bid_vol / ask_vol if ask_vol else 1.0
    except Exception:
        return 1.0


# -------------------------------------------------
# SPOOFING DETECTION
# -------------------------------------------------
def detect_orderbook_spoofing(symbol, depth=10):
    try:
        ob = exchange.fetch_order_book(symbol, limit=depth)
        total = sum(b[1] for b in ob["bids"]) + sum(a[1] for a in ob["asks"])

        if symbol not in ORDERBOOK_HISTORY:
            ORDERBOOK_HISTORY[symbol] = deque(maxlen=SPOOF_WINDOW)

        ORDERBOOK_HISTORY[symbol].append(total)

        if len(ORDERBOOK_HISTORY[symbol]) < SPOOF_WINDOW:
            return False

        max_vol = max(ORDERBOOK_HISTORY[symbol])
        cur = ORDERBOOK_HISTORY[symbol][-1]

        return max_vol > 0 and (max_vol - cur) / max_vol > SPOOF_THRESHOLD
    except Exception:
        return False


# -------------------------------------------------
# VWAP σ BANDS
# -------------------------------------------------
def get_vwap_bands(symbol, timeframe="1m", lookback=30):
    key = f"{symbol}_{timeframe}"
    now = _now()

    if key in VWAP_CACHE and now - VWAP_CACHE[key]["ts"] < VWAP_TTL:
        return VWAP_CACHE[key]["value"]

    candles = exchange.fetch_ohlcv(symbol, timeframe, limit=lookback)
    prices = np.array([(c[2] + c[3] + c[4]) / 3 for c in candles])
    volumes = np.array([c[5] for c in candles])

    vwap = np.sum(prices * volumes) / np.sum(volumes)
    std = np.std(prices)

    bands = {
        "vwap": vwap,
        "upper_1": vwap + std,
        "upper_2": vwap + 2 * std,
        "lower_1": vwap - std,
        "lower_2": vwap - 2 * std
    }

    VWAP_CACHE[key] = {"value": bands, "ts": now}
    return bands


# -------------------------------------------------
# HTF SUPPORT / RESISTANCE
# -------------------------------------------------
def htf_support_resistance(symbol, timeframe="15m", lookback=50):
    try:
        candles = exchange.fetch_ohlcv(symbol, timeframe, limit=lookback)
        highs = [c[2] for c in candles]
        lows = [c[3] for c in candles]
        return min(lows), max(highs)
    except Exception:
        return None, None
