"""
Daily Report — run at midnight via cron
========================================
1. Reads today's JSONL trade log
2. Formats summary
3. Sends to Telegram
4. Moves JSONL to logs/weekly/YYYY-WXX/ folder

Cron: 0 0 * * * cd /path/to/polymarket_flipper && python -m reports.daily_report
"""

import sys
import shutil
import logging
from datetime import date, timedelta
from pathlib import Path

# Allow running from polymarket_flipper/ root
sys.path.insert(0, str(Path(__file__).parent.parent))

import trade_logger as tl
import bankroll as br

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def _week_dir(for_date: date) -> Path:
    """Return logs/weekly/YYYY-WXX/ path for given date."""
    iso = for_date.isocalendar()
    week_label = f"{iso[0]}-W{iso[1]:02d}"
    d = tl.WEEKLY_DIR / week_label
    d.mkdir(parents=True, exist_ok=True)
    return d


def _send_telegram(message: str):
    """Send message via Telegram bot. Reads token + chat_id from env."""
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
        logger.info("Daily report sent to Telegram.")
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")


def send_daily_report(report_date: date = None):
    """
    Generate + send daily report for report_date (defaults to yesterday,
    since this runs at midnight after the day ends).
    """
    target = report_date or (date.today() - timedelta(days=1))
    ds     = target.isoformat()

    summary  = tl.get_daily_summary(ds)
    balance  = br.get_balance()
    message  = tl.format_daily_message(summary, balance_gbp=balance)

    logger.info(f"Daily report for {ds}: {summary['closes']} closed trades, P&L £{summary['pnl_gbp']:.2f}")
    _send_telegram(message)

    # Move JSONL to weekly folder
    src = tl.TRADES_DIR / f"{ds}.jsonl"
    if src.exists():
        dst = _week_dir(target) / f"{ds}.jsonl"
        shutil.move(str(src), str(dst))
        logger.info(f"Moved {src.name} → {dst}")
    else:
        logger.info(f"No trade file for {ds} — nothing to move.")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
    send_daily_report()
