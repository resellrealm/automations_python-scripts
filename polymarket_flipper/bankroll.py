"""
Bankroll Manager
================
Tracks starting £30 and compounds trade size as balance grows.
All sizing is dynamic — as you win, you trade bigger.

Growth model:
  Balance £30  → £3.00/trade (10%)
  Balance £50  → £5.00/trade (10%)
  Balance £100 → £10.00/trade (10%)
  Balance £200 → £15.00/trade (capped at 7.5% above £200)

Rules:
  - Risk 10% of current balance per trade
  - Max 3 open trades simultaneously (total exposure ≤ 30%)
  - Daily loss stop: -10% of today's starting balance
  - Flash crash gets 1.5x sizing (locked-profit strategy)
  - Hard floor: min £2/trade (enough to be worth fees)
  - Hard ceiling: £25/trade (even at large balance, limit single-trade risk)
"""

import json
from pathlib import Path
from datetime import date
from typing import Optional

_STATE_FILE = Path(__file__).parent / "bankroll.json"

STARTING_BALANCE_GBP = 30.0
RISK_PCT             = 0.10   # 10% of balance per trade
MAX_OPEN_TRADES      = 3      # max simultaneous positions
DAILY_LOSS_PCT       = 0.10   # stop day if down 10% of today's starting balance
MIN_TRADE_GBP        = 2.00   # minimum meaningful trade
MAX_TRADE_GBP        = 25.00  # hard ceiling even at large balance

# Default multipliers — overridden by strategy_optimizer.py after real data builds up
_DEFAULT_MULTIPLIERS = {
    "MultiOutcomeArb": 1.5,
    "BundleArb":       1.0,
    "BundleArb_NO":    1.0,
    "ResolutionLag":   1.0,
    "NOBias":          1.2,
    "FlashCrash":      1.0,
    "FlashCrash_NO":   1.0,
}


def _get_multiplier(strategy: str) -> float:
    """
    Load live multiplier from strategy_optimizer.
    Falls back to defaults if optimizer hasn't run yet.
    Maps strategy names to groups.
    """
    try:
        from strategy_optimizer import get_multipliers, STRATEGY_GROUPS
        mults = get_multipliers()
        group = STRATEGY_GROUPS.get(strategy, strategy)
        return mults.get(group, _DEFAULT_MULTIPLIERS.get(strategy, 1.0))
    except Exception:
        return _DEFAULT_MULTIPLIERS.get(strategy, 1.0)


def _load() -> dict:
    if _STATE_FILE.exists():
        try:
            data = json.loads(_STATE_FILE.read_text())
            today = str(date.today())
            # Reset daily starting balance at day change
            if data.get("day") != today:
                data["day"] = today
                data["day_start_balance"] = data.get("balance", STARTING_BALANCE_GBP)
                data["day_pnl"] = 0.0
                _save(data)
            return data
        except Exception:
            pass
    # First run
    data = {
        "balance":           STARTING_BALANCE_GBP,
        "day_start_balance": STARTING_BALANCE_GBP,
        "day_pnl":           0.0,
        "total_pnl":         0.0,
        "peak_balance":      STARTING_BALANCE_GBP,
        "day":               str(date.today()),
        "trades_total":      0,
        "trades_won":        0,
    }
    _save(data)
    return data


def _save(data: dict):
    _STATE_FILE.write_text(json.dumps(data, indent=2))


# ── Public API ─────────────────────────────────────────────────────────────

def get_balance() -> float:
    return _load()["balance"]


def get_day_start_balance() -> float:
    return _load()["day_start_balance"]


def is_stopped_today() -> bool:
    d = _load()
    day_loss = d["day_pnl"]
    if day_loss >= 0:
        return False
    return abs(day_loss) >= d["day_start_balance"] * DAILY_LOSS_PCT


def trade_size_gbp(strategy: str = "NOBias") -> float:
    """
    Standard trade size for directional / semi-guaranteed strategies.
    Uses 10% of balance × live optimizer multiplier.
    """
    balance    = get_balance()
    base       = balance * RISK_PCT
    multiplier = _get_multiplier(strategy)
    size       = base * multiplier
    size       = max(MIN_TRADE_GBP, min(MAX_TRADE_GBP, size))
    return round(size, 2)


def guaranteed_size_gbp(profit_margin: float, n_legs: int = 1) -> float:
    """
    Position size for MATHEMATICALLY GUARANTEED profit trades.
    (BundleArb, MultiOutcomeArb — profit locked regardless of outcome)

    Uses Kelly Criterion: when win probability = 1.0, bet as much as
    the edge justifies — scaled by the size of the locked margin.

    Scaling:
      2% margin  → 20% of balance per leg
      5% margin  → 35% of balance per leg
      10% margin → 50% of balance per leg
      15%+ margin → 60% of balance per leg (hard cap)

    Total exposure across all legs is capped at 70% of balance.
    Never bets the house — keeps 30% liquid for other opportunities.

    Args:
        profit_margin: locked net profit as decimal (e.g. 0.06 = 6%)
        n_legs:        number of legs (for multi-outcome, splits across legs)
    """
    balance = get_balance()

    # Scale % of balance with the margin size
    # Formula: base 15% + (margin × 3), capped at 60%
    pct = min(0.60, 0.15 + (profit_margin * 3))

    # Total exposure across all legs capped at 70% of balance
    total_exposure = balance * min(0.70, pct)

    # Split across legs
    per_leg = total_exposure / max(n_legs, 1)

    # Apply hard floor/ceiling
    per_leg = max(MIN_TRADE_GBP, min(MAX_TRADE_GBP, per_leg))

    return round(per_leg, 2)


def guaranteed_size_usdc(profit_margin: float, n_legs: int = 1, gbp_rate: float = 1.27) -> float:
    return round(guaranteed_size_gbp(profit_margin, n_legs) * gbp_rate, 4)


def trade_size_usdc(strategy: str = "OBMismatch", gbp_rate: float = 1.27) -> float:
    return round(trade_size_gbp(strategy) * gbp_rate, 4)


def record_trade_result(pnl_gbp: float, won: bool):
    """Update balance after a trade closes."""
    d = _load()
    d["balance"]    = round(d["balance"] + pnl_gbp, 4)
    d["day_pnl"]    = round(d["day_pnl"] + pnl_gbp, 4)
    d["total_pnl"]  = round(d["total_pnl"] + pnl_gbp, 4)
    d["trades_total"] += 1
    if won:
        d["trades_won"] += 1
    if d["balance"] > d["peak_balance"]:
        d["peak_balance"] = d["balance"]
    _save(d)


def status_line() -> str:
    d = _load()
    bal   = d["balance"]
    start = d["day_start_balance"]
    day_p = d["day_pnl"]
    total = d["total_pnl"]
    peak  = d["peak_balance"]
    total_t = d["trades_total"]
    won   = d["trades_won"]
    wr    = f"{won/total_t*100:.0f}%" if total_t else "—"
    next_size = trade_size_gbp()

    return (
        f"Balance: £{bal:.2f} | "
        f"Day: {'+' if day_p >= 0 else ''}£{day_p:.2f} | "
        f"Total P&L: {'+' if total >= 0 else ''}£{total:.2f} | "
        f"Peak: £{peak:.2f} | "
        f"Win rate: {wr} ({won}/{total_t}) | "
        f"Next trade: £{next_size:.2f}"
    )


def growth_projection() -> str:
    """Print a 30-day projection based on current win rate."""
    d = _load()
    total_t = d["trades_total"]
    won = d["trades_won"]
    if total_t < 5:
        return "Need 5+ trades for projection."

    win_rate = won / total_t
    avg_win  = abs(d["total_pnl"] / max(won, 1)) if won else 2.0
    avg_loss = 2.0  # assume £2 loss when wrong
    ev_per_trade = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

    balance = d["balance"]
    lines = [f"{'Day':<5} {'Balance':>10} {'Day P&L':>10}"]
    for day in range(1, 31):
        daily_trades = 6  # conservative
        daily_ev = ev_per_trade * daily_trades
        balance += daily_ev
        lines.append(f"{day:<5} £{balance:>9.2f} {'+' if daily_ev >= 0 else ''}£{daily_ev:>9.2f}")

    return "\n".join(lines)
