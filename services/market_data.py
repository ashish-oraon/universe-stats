import concurrent.futures
import json
from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List, Optional

import requests


@dataclass
class TickerStats:
    symbol: str
    yf_symbol: str
    price: Optional[float]
    sma50: Optional[float]
    sma200: Optional[float]
    pct_above_200dma: Optional[float]
    low_52w: Optional[float]
    high_52w: Optional[float]
    pct_from_52w_low: Optional[float]
    pct_from_52w_high: Optional[float]

    def as_dict(self) -> Dict[str, Optional[float]]:
        return asdict(self)


def to_yf_symbol(symbol: str, default_suffix: Optional[str] = None) -> str:
    """
    Convert a raw symbol into a Yahoo symbol.
    Rule: if it has no dot suffix, append .{default_suffix} when provided; otherwise keep as-is.
    """
    symbol = symbol.strip().upper()
    if "." in symbol:
        return symbol
    if default_suffix:
        return f"{symbol}.{default_suffix.upper()}"
    return symbol


def _compute_stats_for_symbol(symbol: str, history_days: int = 420, default_suffix: Optional[str] = None) -> TickerStats:
    yf_symbol = to_yf_symbol(symbol, default_suffix=default_suffix)
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{requests.utils.quote(yf_symbol)}"
        "?range=1y&interval=1d&includePrePost=false&events=div%2Csplit"
    )
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code != 200:
            return TickerStats(symbol=symbol, yf_symbol=yf_symbol, price=None, sma50=None, sma200=None,
                               pct_above_200dma=None, low_52w=None, high_52w=None,
                               pct_from_52w_low=None, pct_from_52w_high=None)
        data = resp.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            return TickerStats(symbol=symbol, yf_symbol=yf_symbol, price=None, sma50=None, sma200=None,
                               pct_above_200dma=None, low_52w=None, high_52w=None,
                               pct_from_52w_low=None, pct_from_52w_high=None)
        series = result[0]
        indicators = series.get("indicators", {})
        quotes = indicators.get("quote", [])
        if not quotes:
            return TickerStats(symbol=symbol, yf_symbol=yf_symbol, price=None, sma50=None, sma200=None,
                               pct_above_200dma=None, low_52w=None, high_52w=None,
                               pct_from_52w_low=None, pct_from_52w_high=None)
        q = quotes[0]
        closes = [float(x) for x in q.get("close", []) if x is not None]
        highs = [float(x) for x in q.get("high", []) if x is not None]
        lows = [float(x) for x in q.get("low", []) if x is not None]
        if not closes:
            return TickerStats(symbol=symbol, yf_symbol=yf_symbol, price=None, sma50=None, sma200=None,
                               pct_above_200dma=None, low_52w=None, high_52w=None,
                               pct_from_52w_low=None, pct_from_52w_high=None)
        price = closes[-1]
        sma50 = sum(closes[-50:]) / 50.0 if len(closes) >= 50 else None
        sma200 = sum(closes[-200:]) / 200.0 if len(closes) >= 200 else None
        pct_above_200dma = None
        if sma200 and sma200 != 0:
            pct_above_200dma = (price - sma200) / sma200 * 100.0
        # 52-week range ~ 252 trading days
        lookback = min(252, len(closes))
        recent_highs = highs[-lookback:] if highs else []
        recent_lows = lows[-lookback:] if lows else []
        low_52w = min(recent_lows) if recent_lows else None
        high_52w = max(recent_highs) if recent_highs else None
        pct_from_52w_low = (price - low_52w) / low_52w * 100.0 if low_52w else None
        pct_from_52w_high = (price - high_52w) / high_52w * 100.0 if high_52w else None
        return TickerStats(
            symbol=symbol,
            yf_symbol=yf_symbol,
            price=price,
            sma50=sma50,
            sma200=sma200,
            pct_above_200dma=pct_above_200dma,
            low_52w=low_52w,
            high_52w=high_52w,
            pct_from_52w_low=pct_from_52w_low,
            pct_from_52w_high=pct_from_52w_high,
        )
    except Exception:
        return TickerStats(symbol=symbol, yf_symbol=yf_symbol, price=None, sma50=None, sma200=None,
                           pct_above_200dma=None, low_52w=None, high_52w=None,
                           pct_from_52w_low=None, pct_from_52w_high=None)


def fetch_stats_for_symbols(symbols: Iterable[str], max_workers: int = 8, default_suffix: Optional[str] = None) -> List[TickerStats]:
    """
    Fetch stats for a collection of symbols concurrently.
    """
    unique_symbols = [s for s in dict.fromkeys(symbols)]  # preserve order, dedupe
    results: List[TickerStats] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(_compute_stats_for_symbol, s, 420, default_suffix): s for s in unique_symbols}
        for fut in concurrent.futures.as_completed(future_map):
            res = fut.result()
            results.append(res)
    # Restore original order by sorting using index in unique_symbols
    index_map = {s: i for i, s in enumerate(unique_symbols)}
    results.sort(key=lambda r: index_map.get(r.symbol, 10**9))
    return results


