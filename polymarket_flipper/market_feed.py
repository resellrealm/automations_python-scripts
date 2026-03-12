"""
Market data fetcher — Gamma API + CLOB orderbook.
Fetches active 15-min crypto markets and live orderbook data.
"""
import requests
from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

GAMMA_URL  = "https://gamma-api.polymarket.com"
CLOB_URL   = "https://clob.polymarket.com"


@dataclass
class TokenInfo:
    token_id:    str
    market_id:   str
    question:    str
    outcome:     str           # "YES" or "NO"
    best_bid:    float = 0.0
    best_ask:    float = 0.0
    mid_price:   float = 0.0
    spread:      float = 0.0
    volume_24h:  float = 0.0
    liquidity:   float = 0.0
    end_time:    Optional[datetime] = None
    extra:       dict = field(default_factory=dict)


def fetch_active_markets(limit: int = 100, keyword: str = "") -> List[dict]:
    """Fetch active markets from Gamma API."""
    params = {
        "active": "true",
        "closed": "false",
        "limit": limit,
    }
    if keyword:
        params["tag"] = keyword
    try:
        r = requests.get(f"{GAMMA_URL}/markets", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"Gamma API error: {e}")
        return []


def fetch_crypto_15min_markets() -> List[dict]:
    """Fetch active 15-minute BTC/ETH/SOL markets."""
    markets = []
    for tag in ["crypto", "bitcoin", "ethereum"]:
        batch = fetch_active_markets(limit=50, keyword=tag)
        markets.extend(batch)

    # Filter for 15-min markets
    filtered = []
    seen = set()
    for m in markets:
        mid = m.get("id") or m.get("conditionId", "")
        if mid in seen:
            continue
        q = (m.get("question") or "").lower()
        if any(w in q for w in ["15", "15-min", "15min"]):
            filtered.append(m)
            seen.add(mid)
    return filtered


def fetch_all_markets(limit: int = 200) -> List[dict]:
    """Fetch a broad set of active markets for NO bias strategy."""
    return fetch_active_markets(limit=limit)


def fetch_orderbook(token_id: str) -> dict:
    """Fetch CLOB orderbook for a token."""
    try:
        r = requests.get(
            f"{CLOB_URL}/book",
            params={"token_id": token_id},
            timeout=5
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.debug(f"Orderbook fetch failed for {token_id}: {e}")
        return {}


def fetch_price(token_id: str) -> dict:
    """Fetch current price for a token."""
    try:
        r = requests.get(
            f"{CLOB_URL}/price",
            params={"token_id": token_id, "side": "buy"},
            timeout=5
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


def parse_orderbook_prices(book: dict) -> tuple:
    """Extract best bid, best ask from orderbook dict."""
    bids = book.get("bids", [])
    asks = book.get("asks", [])
    best_bid = float(bids[0]["price"]) if bids else 0.0
    best_ask = float(asks[0]["price"]) if asks else 0.0
    return best_bid, best_ask


def bid_ask_volume(book: dict, levels: int = 3) -> tuple:
    """Sum top N bid and ask sizes to detect imbalance."""
    bids = book.get("bids", [])[:levels]
    asks = book.get("asks", [])[:levels]
    bid_vol = sum(float(b.get("size", 0)) for b in bids)
    ask_vol = sum(float(a.get("size", 0)) for a in asks)
    return bid_vol, ask_vol


def market_to_tokens(market: dict) -> List[dict]:
    """Extract YES/NO token info from a market dict."""
    tokens = market.get("tokens", []) or market.get("clob_token_ids", [])
    outcomes = market.get("outcomes", ["YES", "NO"])
    if not tokens:
        return []
    result = []
    for i, tok in enumerate(tokens):
        outcome = outcomes[i] if i < len(outcomes) else ("YES" if i == 0 else "NO")
        token_id = tok if isinstance(tok, str) else tok.get("token_id", "")
        result.append({"token_id": token_id, "outcome": outcome})
    return result


def seconds_to_close(market: dict) -> Optional[float]:
    """Return seconds until market end, or None."""
    end = market.get("endDate") or market.get("end_date_iso") or market.get("endDateIso")
    if not end:
        return None
    try:
        if isinstance(end, str):
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
        else:
            end_dt = end
        return (end_dt - datetime.now(timezone.utc)).total_seconds()
    except Exception:
        return None


def build_token_info(market: dict, token: dict, book: dict) -> TokenInfo:
    """Build a TokenInfo object from market + orderbook data."""
    best_bid, best_ask = parse_orderbook_prices(book)
    mid = round((best_bid + best_ask) / 2, 4) if best_bid and best_ask else 0.0
    spread = round(best_ask - best_bid, 4) if best_bid and best_ask else 0.0
    end_raw = market.get("endDate") or market.get("end_date_iso")
    end_dt = None
    if end_raw:
        try:
            end_dt = datetime.fromisoformat(str(end_raw).replace("Z", "+00:00"))
        except Exception:
            pass
    return TokenInfo(
        token_id   = token["token_id"],
        market_id  = market.get("id") or market.get("conditionId", ""),
        question   = market.get("question", ""),
        outcome    = token.get("outcome", "YES"),
        best_bid   = best_bid,
        best_ask   = best_ask,
        mid_price  = mid,
        spread     = spread,
        volume_24h = float(market.get("volume24hr") or market.get("volumeNum") or 0),
        liquidity  = float(market.get("liquidityNum") or market.get("liquidity") or 0),
        end_time   = end_dt,
        extra      = market,
    )
