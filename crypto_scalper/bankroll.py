"""
Bankroll Manager — Crypto Scalper
===================================
Confidence-tiered sizing:
  < 0.45   → skip
  0.45–0.60 → £0.50
  0.60–0.75 → £0.75
  0.75–0.90 → £1.00
  > 0.90   → £1.50
"""
import json
import logging
from pathlib import Path
from datetime import date, datetime, timedelta

from config import SIZING_TIERS, MIN_CONFIDENCE, GBP_TO_USDT, DAILY_LOSS_GBP, COOLDOWN_MINUTES

logger = logging.getLogger(__name__)

_STATE_FILE          = Path(__file__).parent / "bankroll.json"
STARTING_BALANCE_GBP = 50.0


def _load() -> dict:
    if _STATE_FILE.exists():
        try:
            data  = json.loads(_STATE_FILE.read_text())
            today = str(date.today())
            if data.get("day") != today:
                data["day"]               = today
                data["day_start_balance"] = data.get("balance", STARTING_BALANCE_GBP)
                data["day_pnl"]           = 0.0
                data["day_trades"]        = 0
                data["stopped_today"]     = False
                data["cooldown_until"]    = ""
                _save(data)
            return data
        except Exception:
            pass
    data = {
        "balance":           STARTING_BALANCE_GBP,
        "day_start_balance": STARTING_BALANCE_GBP,
        "day_pnl":           0.0,
        "day_trades":        0,
        "total_pnl":         0.0,
        "peak_balance":      STARTING_BALANCE_GBP,
        "trades_total":      0,
        "trades_won":        0,
        "day":               str(date.today()),
        "stopped_today":     False,
        "cooldown_until":    "",
    }
    _save(data)
    return data


def _save(data: dict):
    _STATE_FILE.write_text(json.dumps(data, indent=2))


def get_balance() -> float:
    return _load()["balance"]


def size_for_confidence(confidence: float) -> float:
    if confidence < MIN_CONFIDENCE:
        return 0.0
    for lo, hi, size in SIZING_TIERS:
        if lo <= confidence < hi:
            return size
    return SIZING_TIERS[-1][2]


def size_usdt(confidence: float) -> float:
    return round(size_for_confidence(confidence) * GBP_TO_USDT, 4)


def is_stopped_today() -> bool:
    d = _load()
    if d.get("stopped_today"):
        return True
    if d["day_pnl"] < 0 and abs(d["day_pnl"]) >= DAILY_LOSS_GBP:
        d["stopped_today"]  = True
        d["cooldown_until"] = (datetime.utcnow() + timedelta(minutes=COOLDOWN_MINUTES)).isoformat()
        _save(d)
        logger.warning(f"Daily loss limit hit: £{d['day_pnl']:.2f} — stopping for today.")
        return True
    return False


def is_in_cooldown() -> bool:
    d         = _load()
    until_str = d.get("cooldown_until", "")
    if not until_str:
        return False
    try:
        until = datetime.fromisoformat(until_str)
        if datetime.utcnow() < until:
            remaining = int((until - datetime.utcnow()).total_seconds() / 60)
            logger.debug(f"Cooldown active — {remaining}m remaining.")
            return True
        d["cooldown_until"] = ""
        _save(d)
        return False
    except Exception:
        return False


def record_trade_result(pnl_gbp: float, won: bool):
    d = _load()
    d["balance"]      = round(d["balance"]   + pnl_gbp, 4)
    d["day_pnl"]      = round(d["day_pnl"]   + pnl_gbp, 4)
    d["total_pnl"]    = round(d["total_pnl"] + pnl_gbp, 4)
    d["trades_total"] += 1
    d["day_trades"]   += 1
    if won:
        d["trades_won"] += 1
    if d["balance"] > d["peak_balance"]:
        d["peak_balance"] = d["balance"]
    _save(d)


def status_line() -> str:
    d      = _load()
    bal    = d["balance"]
    day_p  = d["day_pnl"]
    total  = d["total_pnl"]
    peak   = d["peak_balance"]
    total_t = d["trades_total"]
    won    = d["trades_won"]
    wr     = f"{won/total_t*100:.0f}%" if total_t else "—"
    return (
        f"Balance: £{bal:.2f} | "
        f"Day: {'+' if day_p >= 0 else ''}£{day_p:.2f} | "
        f"Total P&L: {'+' if total >= 0 else ''}£{total:.2f} | "
        f"Peak: £{peak:.2f} | "
        f"Win rate: {wr} ({won}/{total_t})"
    )
