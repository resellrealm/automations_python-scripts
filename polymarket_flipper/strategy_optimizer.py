"""
Strategy Optimizer — Self-Adjusting Capital Allocation
=======================================================
Watches actual trade results and automatically shifts capital toward
whatever is making the most money and away from what isn't.

How it works:
  1. After every 5 closed trades, reads per-strategy P&L from DB
  2. Calculates actual EV (expected value) per strategy from real results
  3. Normalises EVs into sizing multipliers (0.2x → 3.0x)
  4. High EV strategies get bigger trades, low EV get smaller
  5. Saves multipliers to optimizer.json — bankroll.py loads these

Safety rules:
  - Never fully disable a strategy (min 0.2x) — it might turn around
  - Never exceed 3.0x (prevents over-concentration)
  - Need minimum 3 closed trades before adjusting a strategy
  - If no real data yet: fall back to sensible defaults
  - Rebalances at most once every 30 minutes (avoid thrashing)

Example after 30 trades:
  NOBias:        win_rate=72%, EV=£0.45  → multiplier 2.4x (£5.76/trade at £30)
  ResolutionLag: win_rate=68%, EV=£0.18  → multiplier 1.2x (£2.88/trade)
  BundleArb:     win_rate=45%, EV=£0.04  → multiplier 0.4x (£0.96/trade)
  MultiOutcome:  win_rate=80%, EV=£0.31  → multiplier 1.8x (£4.32/trade)
"""

import json
import time
import logging
from pathlib import Path
from typing import Optional, Dict

import database as db

logger = logging.getLogger(__name__)

STATE_FILE        = Path(__file__).parent / "optimizer.json"
REBALANCE_EVERY   = 1800      # seconds between rebalances (30 min)
MIN_TRADES_TO_ACT = 3         # minimum closed trades before trusting data
MIN_MULTIPLIER    = 0.2       # never go below 0.2x
MAX_MULTIPLIER    = 3.0       # never go above 3.0x

# Strategy groups: BundleArb_NO is paired with BundleArb, treat together
STRATEGY_GROUPS = {
    "BundleArb":       "BundleArb",
    "BundleArb_NO":    "BundleArb",     # paired — same P&L group
    "MultiOutcomeArb": "MultiOutcomeArb",
    "ResolutionLag":   "ResolutionLag",
    "NOBias":          "NOBias",
    "FlashCrash":      "BundleArb",     # legacy name
    "FlashCrash_NO":   "BundleArb",
}

# Default multipliers before enough real data
DEFAULTS = {
    "MultiOutcomeArb": 1.5,   # guaranteed when fires → start higher
    "BundleArb":       1.0,
    "ResolutionLag":   1.0,
    "NOBias":          1.2,   # best documented EV → start slightly higher
}


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"last_rebalance": 0, "multipliers": dict(DEFAULTS)}


def _save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def get_multipliers() -> dict:
    """Return current sizing multipliers. Called by bankroll.py."""
    return _load_state().get("multipliers", dict(DEFAULTS))


def should_rebalance() -> bool:
    state = _load_state()
    return time.time() - state.get("last_rebalance", 0) >= REBALANCE_EVERY


def rebalance():
    """
    Pull real strategy stats from DB and recalculate multipliers.
    Only runs if enough data exists AND cooldown has passed.
    """
    if not should_rebalance():
        return

    raw_stats = db.get_strategy_stats(min_trades=MIN_TRADES_TO_ACT)
    if not raw_stats:
        logger.debug("Optimizer: not enough closed trades yet — using defaults.")
        return

    # Group strategies (BundleArb + BundleArb_NO → one group)
    grouped: dict = {}
    for row in raw_stats:
        group = STRATEGY_GROUPS.get(row["strategy"], row["strategy"])
        if group not in grouped:
            grouped[group] = {"ev": 0.0, "total": 0, "total_pnl": 0.0}
        grouped[group]["ev"]       += row["ev"] * row["total"]   # weighted sum
        grouped[group]["total"]    += row["total"]
        grouped[group]["total_pnl"] += row["total_pnl"]

    # Calculate weighted average EV per group
    evs = {}
    for group, data in grouped.items():
        if data["total"] >= MIN_TRADES_TO_ACT:
            evs[group] = data["ev"] / data["total"]

    if not evs:
        return

    # Normalise EVs into multipliers
    # Approach: scale so that average EV strategy gets 1.0x
    # Strategies above average get proportionally more, below get less
    ev_values  = list(evs.values())
    ev_mean    = sum(ev_values) / len(ev_values)
    ev_max     = max(ev_values)
    ev_min     = min(ev_values)
    ev_range   = max(ev_max - ev_min, 0.001)

    new_multipliers = {}
    for group, ev in evs.items():
        # Linear scale: worst EV → MIN_MULTIPLIER, best EV → MAX_MULTIPLIER
        normalised = (ev - ev_min) / ev_range          # 0.0 → 1.0
        raw_mult   = MIN_MULTIPLIER + normalised * (MAX_MULTIPLIER - MIN_MULTIPLIER)
        new_multipliers[group] = round(raw_mult, 2)

    # For any strategy we don't have data on yet, keep default
    state = _load_state()
    current = state.get("multipliers", dict(DEFAULTS))
    for group, default_mult in DEFAULTS.items():
        if group not in new_multipliers:
            new_multipliers[group] = current.get(group, default_mult)

    # Log the rebalance
    logger.info("=" * 55)
    logger.info("  Strategy Optimizer — Rebalancing")
    for group in sorted(new_multipliers.keys()):
        ev  = evs.get(group, 0)
        old = current.get(group, DEFAULTS.get(group, 1.0))
        new = new_multipliers[group]
        arrow = "↑" if new > old + 0.05 else ("↓" if new < old - 0.05 else "→")
        trades = grouped.get(group, {}).get("total", 0)
        logger.info(
            f"  {group:<18} EV=${ev:+.4f} | {old:.2f}x {arrow} {new:.2f}x "
            f"({trades} trades)"
        )
    logger.info("=" * 55)

    state["multipliers"]    = new_multipliers
    state["last_rebalance"] = time.time()
    _save_state(state)


def strategy_report() -> str:
    """Human-readable report of strategy performance + current multipliers."""
    stats    = db.get_strategy_stats(min_trades=1)
    mults    = get_multipliers()
    lines    = [
        f"\n{'Strategy':<20} {'Trades':>6} {'WinRate':>8} {'AvgEV':>8} {'TotalP&L':>10} {'Mult':>6}",
        "-" * 62,
    ]
    for s in stats:
        group = STRATEGY_GROUPS.get(s["strategy"], s["strategy"])
        mult  = mults.get(group, 1.0)
        lines.append(
            f"{s['strategy']:<20} {s['total']:>6} "
            f"{s['win_rate']*100:>7.1f}% "
            f"${s['ev']:>+7.4f} "
            f"${s['total_pnl']:>9.2f} "
            f"{mult:>5.2f}x"
        )
    if not stats:
        lines.append("  No closed trades yet.")
    return "\n".join(lines)
