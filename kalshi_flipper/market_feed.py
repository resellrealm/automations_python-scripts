"""
Kalshi Market Feed
==================
Fetches markets, orderbooks, and groups multi-outcome series.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class KalshiMarket:
    ticker:       str
    series:       str
    title:        str
    subtitle:     str        # the specific outcome (e.g. "Maya wins Love Island")
    yes_bid:      int = 0    # cents
    yes_ask:      int = 0    # cents
    yes_mid:      float = 0.0
    volume:       int = 0
    open_interest: int = 0
    close_time:   Optional[datetime] = None
    status:       str = "open"
    result:       Optional[str] = None   # "yes" | "no" | None


@dataclass
class MarketSeries:
    """A group of markets sharing the same series (multi-outcome event)."""
    series_ticker: str
    title:        str
    markets:      List[KalshiMarket] = field(default_factory=list)

    @property
    def yes_sum(self) -> float:
        """Sum of all YES mid prices. If > 1.0, NO bundle arb exists."""
        return sum(m.yes_mid for m in self.markets)

    @property
    def no_bundle_edge(self) -> float:
        """
        Edge from buying NO on all outcomes.
        = yes_sum - 1.0 (before fees)
        Positive = profit opportunity.
        """
        return self.yes_sum - 1.0

    @property
    def outcome_count(self) -> int:
        return len(self.markets)


def build_market(raw: dict, book: dict = None) -> KalshiMarket:
    """Convert raw Kalshi API market dict to KalshiMarket."""
    ticker  = raw.get("ticker", "")
    series  = raw.get("series_ticker", ticker.rsplit("-", 1)[0])
    title   = raw.get("title", "")
    sub     = raw.get("subtitle", raw.get("market_type", ""))

    # Price from orderbook if available, else from market snapshot
    if book:
        bids = book.get("orderbook", {}).get("yes", [])
        asks = book.get("orderbook", {}).get("no", [])  # NO bids = YES asks
        yes_bid = int(bids[0][0]) if bids else raw.get("yes_bid", 0)
        yes_ask = int(100 - asks[0][0]) if asks else raw.get("yes_ask", 0)
    else:
        yes_bid = raw.get("yes_bid", 0)
        yes_ask = raw.get("yes_ask", 0)

    yes_mid = round(((yes_bid + yes_ask) / 2) / 100, 4) if yes_bid and yes_ask else 0.0

    close_raw = raw.get("close_time") or raw.get("expiration_time")
    close_dt  = None
    if close_raw:
        try:
            close_dt = datetime.fromisoformat(str(close_raw).replace("Z", "+00:00"))
        except Exception:
            pass

    return KalshiMarket(
        ticker       = ticker,
        series       = series,
        title        = title,
        subtitle     = sub,
        yes_bid      = yes_bid,
        yes_ask      = yes_ask,
        yes_mid      = yes_mid,
        volume       = raw.get("volume", 0),
        open_interest= raw.get("open_interest", 0),
        close_time   = close_dt,
        status       = raw.get("status", "open"),
        result       = raw.get("result"),
    )


def fetch_all_markets(client) -> List[KalshiMarket]:
    """Fetch all open markets."""
    markets = []
    cursor  = None
    while True:
        try:
            data    = client.get_markets(limit=200, cursor=cursor, status="open")
            batch   = data.get("markets", [])
            markets.extend(build_market(m) for m in batch)
            cursor  = data.get("cursor")
            if not cursor or not batch:
                break
        except Exception as e:
            logger.error(f"fetch_all_markets error: {e}")
            break
    logger.info(f"Fetched {len(markets)} open Kalshi markets.")
    return markets


def group_by_series(markets: List[KalshiMarket]) -> Dict[str, MarketSeries]:
    """Group markets by series ticker for multi-outcome analysis."""
    series_map: Dict[str, MarketSeries] = {}
    for m in markets:
        if m.series not in series_map:
            series_map[m.series] = MarketSeries(series_ticker=m.series, title=m.title)
        series_map[m.series].markets.append(m)
    return series_map


def fetch_series_with_prices(client, series_ticker: str) -> Optional[MarketSeries]:
    """Fetch all markets in a series with fresh orderbook prices."""
    try:
        raw_markets = client.get_series_markets(series_ticker)
        if not raw_markets:
            return None

        kalshi_markets = []
        for rm in raw_markets:
            if rm.get("status") != "open":
                continue
            try:
                book = client.get_orderbook(rm["ticker"], depth=3)
            except Exception:
                book = None
            kalshi_markets.append(build_market(rm, book))

        if not kalshi_markets:
            return None

        return MarketSeries(
            series_ticker = series_ticker,
            title         = raw_markets[0].get("title", series_ticker),
            markets       = kalshi_markets,
        )
    except Exception as e:
        logger.error(f"fetch_series error {series_ticker}: {e}")
        return None


def find_reality_tv_series(markets: List[KalshiMarket]) -> List[str]:
    """Find series tickers for reality TV markets (Love Island, Survivor, etc.)."""
    tv_keywords = ["love island", "survivor", "amazing race", "dancing", "big brother",
                   "bachelor", "masterchef", "bake off", "x factor", "idol"]
    seen = set()
    series = []
    for m in markets:
        title_lower = m.title.lower()
        if any(kw in title_lower for kw in tv_keywords):
            if m.series not in seen:
                seen.add(m.series)
                series.append(m.series)
    return series


def find_multi_outcome_series(markets: List[KalshiMarket],
                               min_outcomes: int = 3) -> List[str]:
    """Find all series with 3+ outcomes (suitable for NO bundle arb)."""
    grouped = group_by_series(markets)
    return [
        s for s, ms in grouped.items()
        if ms.outcome_count >= min_outcomes
    ]
