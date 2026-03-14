"""
Trade Logger — JSONL file-based trade journal
=============================================
Every open/close appends one JSON line to logs/trades/YYYY-MM-DD.jsonl.
Reports read these files to build daily/weekly/alltime summaries.

Used by executor.py on every place_buy() and close_position() call.
"""

import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

BASE_DIR      = Path(__file__).parent
TRADES_DIR    = BASE_DIR / "logs" / "trades"
WEEKLY_DIR    = BASE_DIR / "logs" / "weekly"
ALLTIME_DIR   = BASE_DIR / "logs" / "alltime"


def _ensure_dirs():
    TRADES_DIR.mkdir(parents=True, exist_ok=True)
    WEEKLY_DIR.mkdir(parents=True, exist_ok=True)
    ALLTIME_DIR.mkdir(parents=True, exist_ok=True)


def _today_file() -> Path:
    _ensure_dirs()
    return TRADES_DIR / f"{date.today().isoformat()}.jsonl"


def _append(path: Path, record: dict):
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")


def log_open(
    trade_id: int,
    strategy: str,
    market_id: str,
    token_id: str,
    side: str,
    size: float,
    entry_price: float,
    reason: str,
):
    """Log a trade open event."""
    record = {
        "ts":          datetime.utcnow().isoformat(),
        "type":        "open",
        "trade_id":    trade_id,
        "strategy":    strategy,
        "market_id":   market_id,
        "token_id":    token_id,
        "side":        side,
        "size":        size,
        "entry_price": entry_price,
        "reason":      reason,
    }
    try:
        _append(_today_file(), record)
    except Exception as e:
        logger.debug(f"trade_logger open error: {e}")


def log_close(
    trade_id: int,
    strategy: str,
    exit_price: float,
    pnl_usdc: float,
    pnl_gbp: float,
    won: bool,
):
    """Log a trade close event."""
    record = {
        "ts":         datetime.utcnow().isoformat(),
        "type":       "close",
        "trade_id":   trade_id,
        "strategy":   strategy,
        "exit_price": exit_price,
        "pnl_usdc":   pnl_usdc,
        "pnl_gbp":    pnl_gbp,
        "won":        won,
    }
    try:
        _append(_today_file(), record)
    except Exception as e:
        logger.debug(f"trade_logger close error: {e}")


def get_daily_summary(date_str: Optional[str] = None) -> dict:
    """
    Read a day's JSONL file and return aggregated stats.
    date_str: 'YYYY-MM-DD' or None for today.
    """
    _ensure_dirs()
    ds   = date_str or date.today().isoformat()
    path = TRADES_DIR / f"{ds}.jsonl"

    summary = {
        "date":       ds,
        "opens":      0,
        "closes":     0,
        "wins":       0,
        "losses":     0,
        "pnl_usdc":   0.0,
        "pnl_gbp":    0.0,
        "strategies": {},
    }

    if not path.exists():
        return summary

    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue

        if rec["type"] == "open":
            summary["opens"] += 1
            strat = rec.get("strategy", "unknown")
            if strat not in summary["strategies"]:
                summary["strategies"][strat] = {"opens": 0, "wins": 0, "losses": 0, "pnl_usdc": 0.0}
            summary["strategies"][strat]["opens"] += 1

        elif rec["type"] == "close":
            summary["closes"] += 1
            pnl = rec.get("pnl_usdc", 0.0)
            summary["pnl_usdc"] = round(summary["pnl_usdc"] + pnl, 4)
            summary["pnl_gbp"]  = round(summary["pnl_gbp"] + rec.get("pnl_gbp", 0.0), 4)
            strat = rec.get("strategy", "unknown")
            if strat not in summary["strategies"]:
                summary["strategies"][strat] = {"opens": 0, "wins": 0, "losses": 0, "pnl_usdc": 0.0}
            if rec.get("won"):
                summary["wins"] += 1
                summary["strategies"][strat]["wins"] += 1
            else:
                summary["losses"] += 1
                summary["strategies"][strat]["losses"] += 1
            summary["strategies"][strat]["pnl_usdc"] = round(
                summary["strategies"][strat]["pnl_usdc"] + pnl, 4
            )

    return summary


def format_daily_message(summary: dict, balance_gbp: float = 0.0) -> str:
    """Format a daily summary as a Telegram-ready message."""
    wr = ""
    if summary["wins"] + summary["losses"] > 0:
        rate = summary["wins"] / (summary["wins"] + summary["losses"]) * 100
        wr   = f"{rate:.0f}%"
    else:
        wr = "—"

    sign_usdc = "+" if summary["pnl_usdc"] >= 0 else ""
    sign_gbp  = "+" if summary["pnl_gbp"] >= 0 else ""

    lines = [
        f"📊 <b>Daily Report — {summary['date']}</b>",
        f"",
        f"Trades opened:  {summary['opens']}",
        f"Trades closed:  {summary['closes']}  ({summary['wins']}W / {summary['losses']}L)",
        f"Win rate:       {wr}",
        f"P&L (USDC):     {sign_usdc}${summary['pnl_usdc']:.2f}",
        f"P&L (GBP):      {sign_gbp}£{summary['pnl_gbp']:.2f}",
    ]
    if balance_gbp:
        lines.append(f"Balance:        £{balance_gbp:.2f}")

    if summary["strategies"]:
        lines.append("")
        lines.append("<b>By strategy:</b>")
        for strat, s in sorted(summary["strategies"].items(), key=lambda x: -x[1]["pnl_usdc"]):
            s_sign = "+" if s["pnl_usdc"] >= 0 else ""
            lines.append(f"  {strat}: {s_sign}${s['pnl_usdc']:.2f}  ({s['wins']}W/{s['losses']}L)")

    return "\n".join(lines)
