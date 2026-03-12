"""
Polymarket Strategies
Borrowed/improved from:
  - discountry/polymarket-trading-bot     → flash_crash
  - lorine93s/polymarket-market-maker-bot → market_maker
  - CarlosIbCu/polymarket-kalshi-btc-*   → arbitrage
  - eiri0k/PolyMarket-AI-agent-trading   → ai_sentiment

Performance context (2026 research):
  - Flash crash arbitrage avg opp: 0.5–3% return, lasts ~2.7s
  - Market making spread: ~1.2% bid-ask on active markets
  - 73% of profits captured by sub-100ms bots (not us, but edge still exists)
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import Optional
from config import Config
from shared.logger import get_logger

logger = get_logger("strategies")


# ── Strategy 1: Flash Crash ───────────────────────────────────────
def flash_crash_signal(market: dict, client) -> Optional[dict]:
    """
    Buy YES when probability drops sharply (flash crash) — wait for recovery.
    Strategy from discountry/polymarket-trading-bot.

    Logic:
      - Get price history for the market
      - If latest candle dropped > FLASH_CRASH_DROP_PCT → BUY
      - Target exit at FLASH_CRASH_TARGET_PCT recovery
    """
    token_id = market.get("clob_token_ids", [None])[0]
    if not token_id:
        return None

    history = client.get_market_history(market.get("id", ""), interval="5m")
    if len(history) < 3:
        return None

    prices = [float(h.get("p", 0)) for h in history[-3:]]
    prev_price  = prices[-2]
    curr_price  = prices[-1]

    if prev_price <= 0:
        return None

    drop_pct = ((prev_price - curr_price) / prev_price) * 100

    if drop_pct >= Config.FLASH_CRASH_DROP_PCT and curr_price > 0.05:
        target = curr_price * (1 + Config.FLASH_CRASH_TARGET_PCT / 100)
        target = min(target, 0.95)  # cap below 95¢
        return {
            "strategy": "flash_crash",
            "action": "BUY",
            "token_id": token_id,
            "price": round(curr_price + 0.01, 2),  # lift by 1¢ to fill faster
            "target_exit": round(target, 2),
            "size": min(Config.MAX_POSITION_USDC / curr_price, Config.MAX_POSITION_USDC),
            "reason": f"Prob dropped {drop_pct:.1f}% in 5m (from {prev_price:.2f} to {curr_price:.2f})",
        }
    return None


# ── Strategy 2: Market Maker ──────────────────────────────────────
def market_maker_quotes(market: dict, client) -> Optional[dict]:
    """
    Post passive bid/ask orders to capture spread.
    Pattern from lorine93s/polymarket-market-maker-bot.

    Edge: ~1.2% avg spread on active markets (2025 data).
    Fill rate: 60-80% passive fills expected.
    """
    tokens = market.get("clob_token_ids", [])
    if not tokens:
        return None
    yes_token = tokens[0]

    spread_data = client.get_spread(yes_token)
    bid, ask = spread_data["bid"], spread_data["ask"]
    spread_pct = spread_data["spread_pct"]

    # Only make markets where spread is wide enough for edge
    if spread_pct < Config.MM_SPREAD_PCT:
        return None

    # Quote tighter than market to get priority
    our_bid = round(bid + 0.01, 2)
    our_ask = round(ask - 0.01, 2)

    if our_bid >= our_ask:
        return None  # no room

    size = min(Config.MAX_POSITION_USDC / 2, Config.MM_INVENTORY_LIMIT / 2)

    return {
        "strategy": "market_maker",
        "action": "QUOTE",
        "token_id": yes_token,
        "our_bid": our_bid,
        "our_ask": our_ask,
        "size": round(size, 2),
        "spread_captured_pct": round((our_ask - our_bid) * 100, 2),
        "reason": f"Market spread={spread_pct:.1f}% | quoting {our_bid:.2f}/{our_ask:.2f}",
    }


# ── Strategy 3: Bundle Arbitrage ─────────────────────────────────
def bundle_arbitrage_check(market: dict, client) -> Optional[dict]:
    """
    YES + NO should sum to ~$1.00. If YES + NO < $0.97 → guaranteed profit.
    Borrowed from CarlosIbCu/polymarket-kalshi-btc-arbitrage-bot.

    Note: In 2026 this window is ~2.7 seconds on average. Fast but real.
    """
    tokens = market.get("clob_token_ids", [])
    if len(tokens) < 2:
        return None

    yes_token, no_token = tokens[0], tokens[1]

    yes_ask = client.get_price(yes_token, "buy")
    no_ask  = client.get_price(no_token,  "buy")

    if yes_ask <= 0 or no_ask <= 0:
        return None

    bundle_cost = yes_ask + no_ask
    # If bundle costs less than $1 → buy both, guaranteed $1 at resolution
    if bundle_cost < (1.0 - Config.MIN_EDGE_PCT / 100):
        edge_pct = ((1.0 - bundle_cost) / bundle_cost) * 100
        size = Config.MAX_POSITION_USDC / 2

        return {
            "strategy": "bundle_arbitrage",
            "action": "ARB",
            "yes_token": yes_token,
            "no_token": no_token,
            "yes_price": yes_ask,
            "no_price": no_ask,
            "bundle_cost": round(bundle_cost, 4),
            "edge_pct": round(edge_pct, 2),
            "size": round(size, 2),
            "reason": f"YES({yes_ask:.2f}) + NO({no_ask:.2f}) = {bundle_cost:.2f} < $1.00 | edge={edge_pct:.2f}%",
        }
    return None


# ── Strategy 4: AI Sentiment ──────────────────────────────────────
def ai_sentiment_signal(market: dict, client, ai_client) -> Optional[dict]:
    """
    Use Kimi AI to assess market question + current price vs fair value.
    Ultra-token-efficient: single call, ~200 input tokens, ~80 output.
    Pattern from eiri0k/PolyMarket-AI-agent-trading.
    """
    question    = market.get("question", "")
    end_date    = market.get("end_date_iso", "")
    tokens      = market.get("clob_token_ids", [])
    if not question or not tokens:
        return None

    yes_token   = tokens[0]
    mid         = client.get_midpoint(yes_token)
    if mid <= 0:
        return None

    prompt = (
        f"Market: \"{question}\" (resolves {end_date[:10]}). "
        f"Current YES price: {mid:.2f} (= {mid*100:.0f}% implied probability). "
        f"Is this mispriced? Reply JSON: "
        '{"fair_prob":0-1,"edge":"BUY"|"SELL"|"PASS","confidence":0-1,"reason":"<20 words"}'
    )

    try:
        result = ai_client.chat_json(prompt, temperature=0.2, max_tokens=100)
        fair   = float(result.get("fair_prob", mid))
        edge   = result.get("edge", "PASS")
        conf   = float(result.get("confidence", 0))

        edge_pct = abs(fair - mid) * 100

        if edge in ("BUY", "SELL") and edge_pct >= Config.MIN_EDGE_PCT and conf >= 0.7:
            size = Config.MAX_POSITION_USDC
            return {
                "strategy": "ai_sentiment",
                "action": edge,
                "token_id": yes_token,
                "price": round(mid - 0.01 if edge == "BUY" else mid + 0.01, 2),
                "size": round(size, 2),
                "edge_pct": round(edge_pct, 2),
                "reason": result.get("reason", ""),
            }
    except Exception as e:
        logger.debug(f"AI sentiment error: {e}")
    return None
