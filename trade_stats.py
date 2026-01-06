trade_stats = {}  # symbol -> {wins, losses}

def record_trade(symbol, result):
    if symbol not in trade_stats:
        trade_stats[symbol] = {"wins": 0, "losses": 0}

    trade_stats[symbol][result] += 1

def win_rate(symbol):
    stats = trade_stats.get(symbol)
    if not stats:
        return 0

    total = stats["wins"] + stats["losses"]
    return round((stats["wins"] / total) * 100, 2) if total > 0 else 0
