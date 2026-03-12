"""
Kalshi API Client
==================
Handles RSA authentication and all API calls.
Auth: sign each request with your RSA private key.

Docs: https://docs.kalshi.com
"""

import time
import base64
import hashlib
import logging
import requests
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _load_private_key(path: str):
    """Load RSA private key from PEM file."""
    try:
        from cryptography.hazmat.primitives import serialization
        pem = Path(path).read_bytes()
        return serialization.load_pem_private_key(pem, password=None)
    except ImportError:
        raise RuntimeError("pip install cryptography  — required for Kalshi RSA auth")
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Kalshi private key not found at: {path}\n"
            f"Generate one:\n"
            f"  openssl genrsa -out kalshi_private.pem 2048\n"
            f"  openssl rsa -in kalshi_private.pem -pubout -out kalshi_public.pem\n"
            f"Then upload kalshi_public.pem in your Kalshi account settings."
        )


class KalshiClient:
    """
    Authenticated Kalshi REST API client.
    All methods return parsed JSON or raise on error.
    """

    def __init__(self, api_url: str, key_id: str, private_key_path: str):
        self.base_url    = api_url.rstrip("/")
        self.key_id      = key_id
        self._private_key = _load_private_key(private_key_path)
        self.session     = requests.Session()

    def _sign(self, method: str, path: str, body: str = "") -> dict:
        """Generate RSA signature headers for Kalshi auth."""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding

        ts      = str(int(time.time() * 1000))
        msg     = f"{ts}{method.upper()}{path}{body}"
        sig     = self._private_key.sign(msg.encode(), padding.PKCS1v15(), hashes.SHA256())
        sig_b64 = base64.b64encode(sig).decode()

        return {
            "KALSHI-ACCESS-KEY":       self.key_id,
            "KALSHI-ACCESS-TIMESTAMP": ts,
            "KALSHI-ACCESS-SIGNATURE": sig_b64,
            "Content-Type":            "application/json",
        }

    def _get(self, path: str, params: dict = None) -> dict:
        headers = self._sign("GET", path)
        url     = f"{self.base_url}{path}"
        r = self.session.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, body: dict) -> dict:
        import json
        body_str = json.dumps(body)
        headers  = self._sign("POST", path, body_str)
        url      = f"{self.base_url}{path}"
        r = self.session.post(url, headers=headers, data=body_str, timeout=10)
        r.raise_for_status()
        return r.json()

    def _delete(self, path: str) -> dict:
        headers = self._sign("DELETE", path)
        url     = f"{self.base_url}{path}"
        r = self.session.delete(url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()

    # ── Market data ───────────────────────────────────────────

    def get_markets(self, limit: int = 200, cursor: str = None,
                    status: str = "open", series_ticker: str = None) -> dict:
        params = {"limit": limit, "status": status}
        if cursor:
            params["cursor"] = cursor
        if series_ticker:
            params["series_ticker"] = series_ticker
        return self._get("/markets", params)

    def get_market(self, ticker: str) -> dict:
        return self._get(f"/markets/{ticker}")

    def get_orderbook(self, ticker: str, depth: int = 5) -> dict:
        return self._get(f"/markets/{ticker}/orderbook", {"depth": depth})

    def get_series(self, series_ticker: str) -> dict:
        return self._get(f"/series/{series_ticker}")

    def get_series_markets(self, series_ticker: str) -> list:
        """Get all markets in a series (multi-outcome events)."""
        data = self.get_markets(series_ticker=series_ticker, limit=100)
        return data.get("markets", [])

    # ── Trading ───────────────────────────────────────────────

    def get_balance(self) -> float:
        """Return available balance in USD."""
        data = self._get("/portfolio/balance")
        return float(data.get("balance", 0)) / 100  # Kalshi uses cents

    def place_order(self, ticker: str, side: str, count: int,
                    order_type: str = "market", yes_price: int = None) -> dict:
        """
        Place an order.
        side: "yes" or "no"
        count: number of contracts
        yes_price: limit price in cents (1-99), omit for market orders
        """
        body = {
            "ticker":     ticker,
            "client_order_id": f"kf_{int(time.time()*1000)}",
            "type":       order_type,
            "action":     "buy",
            "side":       side,
            "count":      count,
        }
        if yes_price is not None:
            body["yes_price"] = yes_price
        return self._post("/portfolio/orders", body)

    def cancel_order(self, order_id: str) -> dict:
        return self._delete(f"/portfolio/orders/{order_id}")

    def get_positions(self) -> list:
        data = self._get("/portfolio/positions")
        return data.get("market_positions", [])

    def get_fills(self, ticker: str = None) -> list:
        params = {}
        if ticker:
            params["ticker"] = ticker
        data = self._get("/portfolio/fills", params)
        return data.get("fills", [])

    # ── Helpers ───────────────────────────────────────────────

    def calc_fee(self, contracts: int, price_cents: int) -> float:
        """Calculate Kalshi taker fee in dollars."""
        p = price_cents / 100
        return 0.07 * contracts * p * (1 - p)

    def calc_contracts(self, budget_usd: float, price_cents: int) -> int:
        """How many contracts can we buy with budget_usd at price_cents?"""
        if price_cents <= 0:
            return 0
        price_usd = price_cents / 100
        # cost per contract including fee
        fee_per   = self.calc_fee(1, price_cents)
        total_per = price_usd + fee_per
        return max(1, int(budget_usd / total_per))
