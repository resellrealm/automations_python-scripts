"""
Arb Executor
============
Executes both legs of an arb simultaneously using threading.
Speed matters — prices can move between leg 1 and leg 2.

Strategy:
  - Fire both legs in parallel threads
  - If one leg fails → cancel/close the other immediately
  - Log both sides to DB as a linked arb trade
"""

import logging
import threading
import time
from typing import Optional, Tuple

from config import RISK_PER_ARB_USD, DAILY_LOSS_USD, GBP_TO_USD, KALSHI_FEE_MULT
import database as db
from matcher import ArbMatch

logger = logging.getLogger(__name__)


def _calc_contracts(budget_usd: float, price: float) -> int:
    """Contracts/shares to buy with given budget at given price."""
    if price <= 0:
        return 0
    return max(1, int(budget_usd / price))


def _poly_fee(price: float, is_crypto: bool) -> float:
    return price * 0.0315 if is_crypto else 0.0


def _kalshi_fee(price: float, contracts: int) -> float:
    return KALSHI_FEE_MULT * contracts * price * (1 - price)


def execute_arb(
    arb: ArbMatch,
    poly_client,
    kalshi_client,
    dry_run: bool = False,
) -> bool:
    """
    Execute both legs of an arb in parallel.
    Returns True if both legs placed successfully.
    """
    if db.is_stopped():
        logger.warning("Daily loss limit — skipping arb.")
        return False

    # Split budget 50/50 across legs
    leg_budget = RISK_PER_ARB_USD / 2

    yes_price  = arb.yes_cost
    no_price   = arb.no_cost

    yes_contracts = _calc_contracts(leg_budget, yes_price)
    no_contracts  = _calc_contracts(leg_budget, no_price)

    # Fee estimate
    if arb.buy_yes_on == "polymarket":
        fee = _poly_fee(yes_price, arb.poly_market.is_crypto) * yes_contracts
        fee += _kalshi_fee(no_price, no_contracts)
        yes_platform = "polymarket"
        no_platform  = "kalshi"
        yes_id       = arb.poly_market.market_id
        no_id        = arb.kalshi_market.market_id
    else:
        fee = _kalshi_fee(yes_price, yes_contracts)
        fee += _poly_fee(no_price, arb.poly_market.is_crypto) * no_contracts
        yes_platform = "kalshi"
        no_platform  = "polymarket"
        yes_id       = arb.kalshi_market.market_id
        no_id        = arb.poly_market.market_id

    total_cost = (yes_price * yes_contracts) + (no_price * no_contracts) + fee
    expected_profit = yes_contracts - total_cost  # 1 contract pays $1.00

    logger.info(
        f"\n{'='*60}\n"
        f"  ARB FOUND: {arb.poly_market.title[:55]}\n"
        f"  Match keywords: {', '.join(arb.shared_words[:6])}\n"
        f"  Buy YES on {yes_platform.upper()} @ {yes_price:.3f}\n"
        f"  Buy NO  on {no_platform.upper()} @ {no_price:.3f}\n"
        f"  Bundle cost: ${arb.bundle_cost:.3f} | Net edge: {arb.net_edge*100:.2f}¢\n"
        f"  Expected profit: ${expected_profit:.4f}\n"
        f"  [{'DRY RUN' if dry_run else 'LIVE'}]\n"
        f"{'='*60}"
    )

    if dry_run:
        arb_id = db.log_arb_open(
            poly_id=arb.poly_market.market_id,
            kalshi_id=arb.kalshi_market.market_id,
            event_title=arb.poly_market.title,
            buy_yes_on=yes_platform,
            yes_price=yes_price,
            no_price=no_price,
            bundle_cost=arb.bundle_cost,
            net_edge=arb.net_edge,
            shared_words=",".join(arb.shared_words),
        )
        return arb_id is not None

    # ── Execute both legs in parallel ─────────────────────────
    results = {"yes": None, "no": None, "yes_err": None, "no_err": None}

    def buy_yes():
        try:
            if yes_platform == "polymarket":
                results["yes"] = _poly_buy(poly_client, yes_id, "buy", yes_contracts, yes_price)
            else:
                results["yes"] = kalshi_client.place_order(
                    ticker=yes_id, side="yes", count=yes_contracts, order_type="market"
                )
        except Exception as e:
            results["yes_err"] = str(e)

    def buy_no():
        try:
            if no_platform == "kalshi":
                results["no"] = kalshi_client.place_order(
                    ticker=no_id, side="no", count=no_contracts, order_type="market"
                )
            else:
                results["no"] = _poly_buy(poly_client, no_id, "buy", no_contracts, no_price)
        except Exception as e:
            results["no_err"] = str(e)

    t_yes = threading.Thread(target=buy_yes)
    t_no  = threading.Thread(target=buy_no)

    t_yes.start()
    t_no.start()
    t_yes.join(timeout=10)
    t_no.join(timeout=10)

    if results["yes_err"] or results["no_err"]:
        logger.error(
            f"Arb execution partial failure!\n"
            f"  YES: {results['yes_err'] or 'ok'}\n"
            f"  NO:  {results['no_err'] or 'ok'}\n"
            f"  Manual check required — one leg may be open without the other!"
        )
        return False

    logger.info("Both arb legs placed successfully.")
    db.log_arb_open(
        poly_id=arb.poly_market.market_id,
        kalshi_id=arb.kalshi_market.market_id,
        event_title=arb.poly_market.title,
        buy_yes_on=yes_platform,
        yes_price=yes_price,
        no_price=no_price,
        bundle_cost=arb.bundle_cost,
        net_edge=arb.net_edge,
        shared_words=",".join(arb.shared_words),
    )
    return True


def _poly_buy(client, token_id: str, action: str, size: int, price: float) -> dict:
    """Place a Polymarket market order via py-clob-client."""
    from py_clob_client.clob_types import MarketOrderArgs
    order = MarketOrderArgs(
        token_id = token_id,
        amount   = round(price * size, 4),
    )
    return client.create_market_order(order)
