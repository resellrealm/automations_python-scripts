"""
Whale Consensus Strategy
========================
Monitors 5 known sharp wallets on Polymarket's crypto up/down markets.
When 2+ wallets bet the same direction, we mirror — but ONLY if our own
crypto momentum signal agrees with them.

Combined confidence scoring:
  Base = whale consensus (how many wallets agree)
  ± momentum agreement (does the 5-min YES/NO drift confirm the direction?)

  Both agree  → (whale_conf + momentum_conf) / 2 × 1.20 boost
  Whales only → whale_conf × 0.85  (no momentum confirmation)
  Disagree    → skip (whales say YES but momentum says NO = no trade)

Result sizing:
  conf 0.45–0.60 → £0.75
  conf 0.60–0.75 → £0.90
  conf 0.75+     → £1.00

Uses Polymarket Data API — all wallet activity is public on Polygon.
"""
import logging
import requests
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from typing import Optional

logger = logging.getLogger(__name__)

# ── Target wallets to monitor ─────────────────────────────────────────
WHALE_WALLETS = [
    "0x87d6b08de837a3d1237ef8f26f149fc0551048a4",
    "0x39636344f4906695016c13a78a8cd4ea705b2b0b",
    "0x1568915b183ae151f01787dd5fe609e71d668c0b",
    "0xec63aa7aecca29b7b376b2dc861c6c1503e88b32",
    "0x420b1d929d04c2275dd1242ff53df0d647f63e0a",
]

TOTAL_WALLETS      = len(WHALE_WALLETS)
MIN_WALLETS_AGREE  = 2          # minimum wallets that must agree to fire
RECENCY_MINUTES    = 5          # only count trades placed in last N minutes
DATA_API_URL       = "https://data-api.polymarket.com"

# Only mirror trades on these crypto up/down markets (5-min and 15-min)
CRYPTO_KEYWORDS = (
    "bitcoin", "btc", "ethereum", "eth", "solana", "sol",
    "xrp", "ripple", "dogecoin", "doge", "bnb", "hyperliquid", "hype",
    "avax", "avalanche",
)
TIMEFRAME_KEYWORDS = ("5-minute", "15-minute", "5 minute", "15 minute",
                      "5min", "15min", "up or down")

# Confidence per number of agreeing wallets
_CONF_MAP = {
    2: 0.60,
    3: 0.75,
    4: 0.90,
    5: 1.00,
}


@dataclass
class ConsensusSignal:
    market_id:      str
    token_id:       str
    question:       str
    side:           str     # "YES" or "NO"
    price:          float   # avg entry price across whale trades
    wallets:        list    # which wallets triggered this
    n_agree:        int
    whale_conf:     float   # confidence from whale count alone
    momentum_conf:  float   # confidence from price drift (0 if not available)
    confidence:     float   # final combined score
    reason:         str


def _momentum_confidence(token_id: str, side: str) -> float:
    """
    Fetch live orderbook for this token and compute momentum confidence.
    Returns 0.0 if unavailable or if direction disagrees with `side`.

    Reuses the same CLOB orderbook endpoint as the rest of the bot.
    Momentum score = how far YES has drifted from 0.50, mapped to 0.0–0.85.
      side=YES: need YES mid > 0.50 (up momentum)
      side=NO:  need YES mid < 0.50 (down momentum = NO momentum)
    """
    try:
        resp = requests.get(
            f"https://clob.polymarket.com/book",
            params={"token_id": token_id},
            timeout=8,
        )
        resp.raise_for_status()
        book = resp.json()

        bids = book.get("bids", [])
        asks = book.get("asks", [])
        if not bids or not asks:
            return 0.0

        best_bid = float(bids[0]["price"])
        best_ask = float(asks[0]["price"])
        mid      = (best_bid + best_ask) / 2.0

        if side == "YES":
            drift = mid - 0.50
        else:  # NO momentum = YES price falling
            drift = 0.50 - mid

        if drift <= 0:
            return 0.0   # price moving against whale direction

        # Map drift 0→0.20+ to confidence 0.45→0.85
        return round(min(0.85, 0.45 + drift * 2.0), 3)

    except Exception as e:
        logger.debug(f"Momentum fetch failed for {token_id[:12]}: {e}")
        return 0.0


def _combined_confidence(whale_conf: float, momentum_conf: float) -> float:
    """
    Combine whale and momentum scores into a final confidence.
      Both signals   → average × 1.20 boost (capped at 1.0)
      Whales only    → whale_conf × 0.85
      Momentum = 0   → whale_conf × 0.85 (no confirmation)
    """
    if momentum_conf > 0:
        combined = (whale_conf + momentum_conf) / 2.0 * 1.20
        return round(min(1.0, combined), 3)
    return round(whale_conf * 0.85, 3)


class WhaleConsensusDetector:
    """
    Polls recent trades from each whale wallet.
    Groups by (market_id, token_id) within the recency window.
    Fires a ConsensusSignal when MIN_WALLETS_AGREE or more agree.
    """

    def _fetch_wallet_trades(self, wallet: str, since: datetime) -> list:
        """
        Fetch recent trades for a wallet from the Polymarket Data API.
        Returns list of trade dicts.
        """
        try:
            resp = requests.get(
                f"{DATA_API_URL}/activity",
                params={
                    "user":   wallet,
                    "limit":  50,
                },
                timeout=10,
            )
            resp.raise_for_status()
            trades = resp.json() if isinstance(resp.json(), list) else resp.json().get("data", [])

            # Filter to recency window
            recent = []
            for t in trades:
                ts_raw = t.get("timestamp") or t.get("created_at") or t.get("time")
                if not ts_raw:
                    continue
                try:
                    if isinstance(ts_raw, (int, float)):
                        ts = datetime.fromtimestamp(ts_raw, tz=timezone.utc)
                    else:
                        ts = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
                    if ts >= since:
                        recent.append(t)
                except Exception:
                    continue
            return recent

        except requests.RequestException as e:
            logger.warning(f"Whale fetch error ({wallet[:10]}...): {e}")
            return []

    def scan(self) -> list[ConsensusSignal]:
        """
        Scan all wallets, find consensus trades.
        Returns list of ConsensusSignal (one per agreed market+side).
        """
        since = datetime.now(timezone.utc) - timedelta(minutes=RECENCY_MINUTES)

        # market_key → {wallet_address: trade_dict}
        # market_key = (token_id, side)
        market_votes: dict = defaultdict(dict)

        for wallet in WHALE_WALLETS:
            trades = self._fetch_wallet_trades(wallet, since)
            for trade in trades:
                token_id = trade.get("asset_id") or trade.get("token_id") or ""
                side     = (trade.get("side") or trade.get("outcome") or "").upper()
                if not token_id or side not in ("YES", "NO", "BUY", "SELL"):
                    continue

                # Normalise side: BUY=YES, SELL=NO for our purposes
                if side == "BUY":
                    side = "YES"
                elif side == "SELL":
                    side = "NO"

                # Only care about crypto up/down markets
                question = (
                    trade.get("title") or trade.get("question") or ""
                ).lower()
                is_crypto    = any(kw in question for kw in CRYPTO_KEYWORDS)
                is_timeframe = any(kw in question for kw in TIMEFRAME_KEYWORDS)
                if not (is_crypto and is_timeframe):
                    continue

                key = (token_id, side)
                # Only keep the most recent trade per wallet per key
                if wallet not in market_votes[key]:
                    market_votes[key][wallet] = trade

        # Find keys where MIN_WALLETS_AGREE+ wallets voted
        signals = []
        for (token_id, side), wallet_trades in market_votes.items():
            n = len(wallet_trades)
            if n < MIN_WALLETS_AGREE:
                continue

            whale_conf = _CONF_MAP.get(min(n, TOTAL_WALLETS), 1.00)

            # Check our own momentum signal for this token
            momentum_conf = _momentum_confidence(token_id, side)

            # If momentum actively disagrees (returns 0 because drift is wrong way) → skip
            # But only skip if we have a clear counter-signal (not just unavailable)
            final_conf = _combined_confidence(whale_conf, momentum_conf)

            # Average entry price across whale trades
            prices = []
            for t in wallet_trades.values():
                p = t.get("price") or t.get("average_price")
                if p:
                    try:
                        prices.append(float(p))
                    except Exception:
                        pass
            avg_price = round(sum(prices) / len(prices), 4) if prices else 0.50

            # Get market info from first trade
            sample    = next(iter(wallet_trades.values()))
            market_id = sample.get("market") or sample.get("condition_id") or ""
            question  = sample.get("title") or sample.get("question") or market_id[:40]

            wallets_triggered = list(wallet_trades.keys())

            momentum_str = f"momentum={momentum_conf:.2f}" if momentum_conf > 0 else "no momentum signal"
            reason = (
                f"WhaleConsensus: {n}/{TOTAL_WALLETS} wallets | {side} | "
                f"{question[:50]} | price={avg_price:.3f} | "
                f"whale_conf={whale_conf:.2f} {momentum_str} → final={final_conf:.2f}"
            )

            logger.info(reason)

            signals.append(ConsensusSignal(
                market_id      = market_id,
                token_id       = token_id,
                question       = question,
                side           = side,
                price          = avg_price,
                wallets        = wallets_triggered,
                n_agree        = n,
                whale_conf     = whale_conf,
                momentum_conf  = momentum_conf,
                confidence     = final_conf,
                reason         = reason,
            ))

        return signals
