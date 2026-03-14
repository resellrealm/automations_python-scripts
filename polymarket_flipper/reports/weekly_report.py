"""
Weekly Report — run Sunday midnight via cron
=============================================
1. Reads all daily JSONL files in the current week's folder
2. Aggregates into weekly summary
3. Sends Telegram report
4. Appends one line to logs/alltime/weekly_pnl.jsonl
5. Deletes the processed week folder

Cron: 0 0 * * 0 cd /path/to/polymarket_flipper && python -m reports.weekly_report
"""

import sys
import json
import shutil
import logging
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import trade_logger as tl
import bankroll as br

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def _send_telegram(message: str):
    import os
    import requests
    token   = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_USER_ID", "")
    if not token or not chat_id:
        print("[TELEGRAM NOT CONFIGURED] Message:\n" + message)
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
            timeout=10,
        )
        logger.info("Weekly report sent to Telegram.")
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")


def _week_label(for_date: date) -> str:
    iso = for_date.isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def send_weekly_report(for_date: date = None):
    """
    Aggregate last week and send summary.
    Defaults to the week that just ended (today is Monday = yesterday's week).
    """
    target      = for_date or (date.today() - timedelta(days=1))
    week_lbl    = _week_label(target)
    week_folder = tl.WEEKLY_DIR / week_lbl

    # Aggregate all daily files in the week folder
    totals = {
        "week":          week_lbl,
        "trades":        0,
        "wins":          0,
        "losses":        0,
        "pnl_usdc":      0.0,
        "pnl_gbp":       0.0,
        "start_balance": 0.0,   # will fill from first day
        "end_balance":   br.get_balance(),
        "strategies":    {},
    }

    day_summaries = []
    if week_folder.exists():
        for jsonl in sorted(week_folder.glob("*.jsonl")):
            ds  = jsonl.stem
            day = tl.get_daily_summary(None)  # parse from the moved file
            # Re-parse directly from file
            day = _parse_file(jsonl)
            day_summaries.append(day)
            totals["trades"]   += day["closes"]
            totals["wins"]     += day["wins"]
            totals["losses"]   += day["losses"]
            totals["pnl_usdc"] = round(totals["pnl_usdc"] + day["pnl_usdc"], 4)
            totals["pnl_gbp"]  = round(totals["pnl_gbp"]  + day["pnl_gbp"], 4)
            for strat, s in day["strategies"].items():
                if strat not in totals["strategies"]:
                    totals["strategies"][strat] = {"wins": 0, "losses": 0, "pnl_usdc": 0.0}
                totals["strategies"][strat]["wins"]     += s["wins"]
                totals["strategies"][strat]["losses"]   += s["losses"]
                totals["strategies"][strat]["pnl_usdc"] = round(
                    totals["strategies"][strat]["pnl_usdc"] + s["pnl_usdc"], 4
                )

    # Build telegram message
    wr = f"{totals['wins']/(totals['wins']+totals['losses'])*100:.0f}%" if (totals["wins"]+totals["losses"]) > 0 else "—"
    best_strat = max(totals["strategies"].items(), key=lambda x: x[1]["pnl_usdc"])[0] if totals["strategies"] else "—"
    sign_gbp   = "+" if totals["pnl_gbp"] >= 0 else ""
    sign_usdc  = "+" if totals["pnl_usdc"] >= 0 else ""

    message = (
        f"📈 <b>Weekly Report — {week_lbl}</b>\n"
        f"\n"
        f"Closed trades:  {totals['trades']}\n"
        f"Wins / Losses:  {totals['wins']}W / {totals['losses']}L  ({wr})\n"
        f"P&L (USDC):     {sign_usdc}${totals['pnl_usdc']:.2f}\n"
        f"P&L (GBP):      {sign_gbp}£{totals['pnl_gbp']:.2f}\n"
        f"End balance:    £{totals['end_balance']:.2f}\n"
        f"Best strategy:  {best_strat}\n"
    )
    if totals["strategies"]:
        message += "\n<b>By strategy:</b>\n"
        for strat, s in sorted(totals["strategies"].items(), key=lambda x: -x[1]["pnl_usdc"]):
            s_sign = "+" if s["pnl_usdc"] >= 0 else ""
            message += f"  {strat}: {s_sign}${s['pnl_usdc']:.2f}  ({s['wins']}W/{s['losses']}L)\n"

    _send_telegram(message)

    # Append to alltime
    tl._ensure_dirs()
    alltime_file = tl.ALLTIME_DIR / "weekly_pnl.jsonl"
    alltime_record = {
        "week":          totals["week"],
        "trades":        totals["trades"],
        "wins":          totals["wins"],
        "pnl_gbp":       totals["pnl_gbp"],
        "best_strategy": best_strat,
        "end_balance":   totals["end_balance"],
    }
    with open(alltime_file, "a") as f:
        f.write(json.dumps(alltime_record) + "\n")
    logger.info(f"Appended week summary to {alltime_file}")

    # Delete processed weekly folder
    if week_folder.exists():
        shutil.rmtree(week_folder)
        logger.info(f"Deleted processed folder: {week_folder}")


def _parse_file(path: Path) -> dict:
    """Parse a JSONL file and return daily summary dict."""
    summary = {"closes": 0, "wins": 0, "losses": 0, "pnl_usdc": 0.0, "pnl_gbp": 0.0, "strategies": {}}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        if rec["type"] == "close":
            summary["closes"] += 1
            pnl = rec.get("pnl_usdc", 0.0)
            summary["pnl_usdc"] = round(summary["pnl_usdc"] + pnl, 4)
            summary["pnl_gbp"]  = round(summary["pnl_gbp"] + rec.get("pnl_gbp", 0.0), 4)
            strat = rec.get("strategy", "unknown")
            if strat not in summary["strategies"]:
                summary["strategies"][strat] = {"wins": 0, "losses": 0, "pnl_usdc": 0.0}
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


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
    send_weekly_report()
