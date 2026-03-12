"""
Polymarket Market Client
Uses the official py-clob-client SDK.
Patterns borrowed from:
  - Polymarket/agents (official framework)
  - discountry/polymarket-trading-bot (flash crash strategy)
  - lorine93s/polymarket-market-maker-bot (market making)
  - CarlosIbCu/polymarket-kalshi-btc-arbitrage-bot (arbitrage)
"""

import sys, os, time, requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import List, Optional
from config import Config
from shared.logger import get_logger

logger = get_logger("market_client")


class PolymarketClient:
    def __init__(self):
        self.clob = Config.CLOB_HOST
        self.gamma = Config.GAMMA_HOST
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self._clob_client = None
        self._init_clob()

    def _init_clob(self):
        """Initialise the official py-clob-client for authenticated order operations."""
        if not Config.PRIVATE_KEY or Config.PRIVATE_KEY == "0xyour_private_key_here":
            logger.warning("No POLYGON_PRIVATE_KEY set — running in read-only mode.")
            return
        try:
            from py_clob_client.client import ClobClient
            from py_clob_client.constants import POLYGON
            self._clob_client = ClobClient(
                self.clob,
                chain_id=POLYGON,
                private_key=Config.PRIVATE_KEY,
            )
            self._clob_client.create_or_derive_api_creds()
            logger.info("py-clob-client authenticated.")
        except ImportError:
            logger.warning("py-clob-client not installed. Run: pip install py-clob-client")
        except Exception as e:
            logger.error(f"CLOB auth failed: {e}")

    # ── Market data (no auth needed) ─────────────────────────────

    def get_markets(self, limit: int = 100, active_only: bool = True) -> List[dict]:
        """Fetch markets from Gamma API."""
        try:
            params = {"limit": limit, "active": str(active_only).lower(), "order": "volume", "ascending": "false"}
            r = self.session.get(f"{self.gamma}/markets", params=params, timeout=15)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"get_markets failed: {e}")
            return []

    def get_order_book(self, token_id: str) -> dict:
        """Get order book for a market token."""
        try:
            r = self.session.get(f"{self.clob}/book", params={"token_id": token_id}, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"get_order_book failed: {e}")
            return {}

    def get_price(self, token_id: str, side: str = "buy") -> float:
        """Get current price for YES or NO token."""
        try:
            r = self.session.get(
                f"{self.clob}/price",
                params={"token_id": token_id, "side": side},
                timeout=10,
            )
            r.raise_for_status()
            return float(r.json().get("price", 0))
        except Exception as e:
            logger.error(f"get_price failed: {e}")
            return 0.0

    def get_midpoint(self, token_id: str) -> float:
        """Get midpoint price for a token."""
        try:
            r = self.session.get(f"{self.clob}/midpoint", params={"token_id": token_id}, timeout=10)
            r.raise_for_status()
            return float(r.json().get("mid", 0))
        except Exception as e:
            return 0.0

    def get_market_history(self, market_id: str, interval: str = "1h") -> List[dict]:
        """Get historical price data for a market."""
        try:
            r = self.session.get(
                f"{self.gamma}/markets/{market_id}/prices-history",
                params={"interval": interval},
                timeout=15,
            )
            r.raise_for_status()
            return r.json().get("history", [])
        except Exception as e:
            logger.error(f"get_market_history failed: {e}")
            return []

    def get_spread(self, token_id: str) -> dict:
        """Return best bid, best ask, and spread for a token."""
        book = self.get_order_book(token_id)
        bids = sorted(book.get("bids", []), key=lambda x: float(x.get("price", 0)), reverse=True)
        asks = sorted(book.get("asks", []), key=lambda x: float(x.get("price", 0)))
        best_bid = float(bids[0]["price"]) if bids else 0
        best_ask = float(asks[0]["price"]) if asks else 1
        spread   = best_ask - best_bid
        return {"bid": best_bid, "ask": best_ask, "spread": spread, "spread_pct": spread * 100}

    # ── Order operations (auth required) ─────────────────────────

    def buy(self, token_id: str, price: float, size: float) -> dict:
        """Place a BUY order (real or simulated)."""
        if Config.DRY_RUN:
            order = {"dry_run": True, "token_id": token_id, "price": price, "size": size, "side": "BUY"}
            logger.info(f"[DRY RUN] BUY {size} USDC of token {token_id[:12]}... @ {price}")
            return order

        if not self._clob_client:
            raise RuntimeError("CLOB client not authenticated")

        from py_clob_client.order_builder.constants import BUY
        from py_clob_client.clob_types import OrderArgs
        order_args = OrderArgs(price=price, size=size, side=BUY, token_id=token_id)
        resp = self._clob_client.create_and_post_order(order_args)
        logger.info(f"BUY order placed: {resp}")
        return resp

    def sell(self, token_id: str, price: float, size: float) -> dict:
        """Place a SELL order (real or simulated)."""
        if Config.DRY_RUN:
            order = {"dry_run": True, "token_id": token_id, "price": price, "size": size, "side": "SELL"}
            logger.info(f"[DRY RUN] SELL {size} of token {token_id[:12]}... @ {price}")
            return order

        if not self._clob_client:
            raise RuntimeError("CLOB client not authenticated")

        from py_clob_client.order_builder.constants import SELL
        from py_clob_client.clob_types import OrderArgs
        order_args = OrderArgs(price=price, size=size, side=SELL, token_id=token_id)
        resp = self._clob_client.create_and_post_order(order_args)
        logger.info(f"SELL order placed: {resp}")
        return resp

    def cancel_all(self):
        """Cancel all open orders."""
        if Config.DRY_RUN:
            logger.info("[DRY RUN] Cancel all orders")
            return
        if self._clob_client:
            self._clob_client.cancel_all()
