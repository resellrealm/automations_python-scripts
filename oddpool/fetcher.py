"""
Market Fetcher
==============
Fetches live YES prices from both Polymarket and Kalshi.
Returns normalised MarketSnapshot objects for comparison.
"""

import logging
import requests
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MarketSnapshot:
    platform:   str          # "polymarket" | "kalshi"
    market_id:  str          # internal ID / ticker
    title:      str          # human-readable question
    yes_bid:    float        # best bid for YES (what you receive if you sell YES)
    yes_ask:    float        # best ask for YES (what you pay to buy YES)
    no_bid:     float        # = 1 - yes_ask
    no_ask:     float        # = 1 - yes_bid
    volume_24h: float
    is_crypto:  bool = False  # affects fee on Polymarket

    @property
    def yes_mid(self) -> float:
        return round((self.yes_bid + self.yes_ask) / 2, 4)

    @property
    def no_mid(self) -> float:
        return round(1.0 - self.yes_mid, 4)


# ── Polymarket ────────────────────────────────────────────────

POLY_CRYPTO_KEYWORDS = ["btc", "bitcoin", "eth", "ethereum", "sol", "solana", "crypto"]

def _is_crypto(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in POLY_CRYPTO_KEYWORDS)


def fetch_polymarket_markets(limit: int = 300) -> List[MarketSnapshot]:
    """Fetch active Polymarket markets with prices."""
    markets = []
    try:
        r = requests.get(
            "https://gamma-api.polymarket.com/markets",
            params={"active": "true", "closed": "false", "limit": limit},
            timeout=12,
        )
        r.raise_for_status()
        raw = r.json()
        if isinstance(raw, dict):
            raw = raw.get("markets", [])

        for m in raw:
            token_ids = m.get("tokens") or m.get("clob_token_ids") or []
            if not token_ids:
                continue
            tok = token_ids[0]
            tok_id = tok if isinstance(tok, str) else tok.get("token_id", "")

            # Get orderbook prices
            try:
                book_r = requests.get(
                    "https://clob.polymarket.com/book",
                    params={"token_id": tok_id},
                    timeout=5,
                )
                book = book_r.json() if book_r.ok else {}
            except Exception:
                book = {}

            bids = book.get("bids", [])
            asks = book.get("asks", [])
            yes_bid = float(bids[0]["price"]) if bids else 0.0
            yes_ask = float(asks[0]["price"]) if asks else 0.0

            if not yes_bid or not yes_ask:
                continue

            title = m.get("question") or m.get("title") or ""
            markets.append(MarketSnapshot(
                platform   = "polymarket",
                market_id  = tok_id,
                title      = title,
                yes_bid    = yes_bid,
                yes_ask    = yes_ask,
                no_bid     = round(1.0 - yes_ask, 4),
                no_ask     = round(1.0 - yes_bid, 4),
                volume_24h = float(m.get("volume24hr") or m.get("volumeNum") or 0),
                is_crypto  = _is_crypto(title),
            ))

    except Exception as e:
        logger.error(f"Polymarket fetch error: {e}")

    logger.info(f"Fetched {len(markets)} Polymarket markets.")
    return markets


# ── Kalshi ────────────────────────────────────────────────────

def fetch_kalshi_markets(client) -> List[MarketSnapshot]:
    """Fetch open Kalshi markets with prices."""
    markets = []
    cursor  = None

    while True:
        try:
            data   = client.get_markets(limit=200, cursor=cursor, status="open")
            batch  = data.get("markets", [])
            cursor = data.get("cursor")

            for m in batch:
                yes_bid = m.get("yes_bid", 0)
                yes_ask = m.get("yes_ask", 0)
                if not yes_bid or not yes_ask:
                    continue

                yes_bid_f = yes_bid / 100
                yes_ask_f = yes_ask / 100

                title = m.get("title") or m.get("subtitle") or ""
                markets.append(MarketSnapshot(
                    platform   = "kalshi",
                    market_id  = m.get("ticker", ""),
                    title      = title,
                    yes_bid    = yes_bid_f,
                    yes_ask    = yes_ask_f,
                    no_bid     = round(1.0 - yes_ask_f, 4),
                    no_ask     = round(1.0 - yes_bid_f, 4),
                    volume_24h = float(m.get("volume", 0)),
                    is_crypto  = _is_crypto(title),
                ))

            if not cursor or not batch:
                break

        except Exception as e:
            logger.error(f"Kalshi fetch error: {e}")
            break

    logger.info(f"Fetched {len(markets)} Kalshi markets.")
    return markets
