"""
Telegram Push — Proactive VPS Notifier
=======================================
Sends messages TO YOU directly via the Telegram Bot API.
NO polling. NO waiting for you to message first.
Works from ANY script on the VPS — just import and call notify().

This is SEPARATE from the OpenClaw bot (telegram_messenger/bot.py).
The bot responds when you message it.
THIS module pushes to you whenever the VPS wants to.

Usage (import from any script):
    from telegram_push import notify
    notify("Hello from VPS!")

    from telegram_push import notify_task_done
    notify_task_done("Scrape Jobs", output="Found 47 listings")

Standalone CLI:
    python telegram_push/push.py "Hello from VPS"
    python telegram_push/push.py --task-done "Scrape Jobs" --output "Found 47"
    python telegram_push/push.py --task-fail "Scrape Jobs" --error "Connection refused"
    python telegram_push/push.py --crash "polymarket bot" --log "flipper.log"
    python telegram_push/push.py --status

How it works:
    requests.post("https://api.telegram.org/bot{TOKEN}/sendMessage", ...)
    → Telegram delivers straight to your phone
    → No bot polling loop required
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path

import requests

# ── Config ────────────────────────────────────────────────────────────────────
# Load from .env if present, otherwise read from environment
def _load_env():
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        # Try repo root .env
        env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())

_load_env()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT  = os.getenv("TELEGRAM_USER_ID", "") or os.getenv("TELEGRAM_CHAT_ID", "")

logger = logging.getLogger(__name__)


# ── Core send ─────────────────────────────────────────────────────────────────

def _send(text: str, parse_mode: str = "HTML") -> bool:
    """
    Send a message directly to your Telegram.
    Returns True on success, False on failure.
    Bypasses the bot polling loop entirely.
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        logger.warning(
            "[telegram_push] Not configured. Set TELEGRAM_BOT_TOKEN and "
            "TELEGRAM_USER_ID in your .env file."
        )
        print(f"[telegram_push] NOT SENT (no config): {text[:100]}")
        return False

    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id":    TELEGRAM_CHAT,
                "text":       text[:4096],   # Telegram max length
                "parse_mode": parse_mode,
            },
            timeout=10,
        )
        if not resp.ok:
            logger.warning(f"[telegram_push] API error {resp.status_code}: {resp.text[:200]}")
            return False
        return True
    except Exception as e:
        logger.error(f"[telegram_push] Send failed: {e}")
        return False


# ── Public API ────────────────────────────────────────────────────────────────

def notify(message: str) -> bool:
    """Send any plain message. Use HTML tags for formatting."""
    return _send(message)


def notify_task_start(task_name: str, cmd: str = "") -> bool:
    """Call this when a background task starts."""
    msg = f"⏳ <b>Task started</b>: {task_name}"
    if cmd:
        msg += f"\n<code>{cmd[:200]}</code>"
    msg += f"\n<i>{datetime.now().strftime('%H:%M:%S')}</i>"
    return _send(msg)


def notify_task_done(task_name: str, output: str = "", duration_s: float = 0) -> bool:
    """Call this when a background task completes successfully."""
    msg = f"✅ <b>Task done</b>: {task_name}"
    if duration_s:
        mins = int(duration_s // 60)
        secs = int(duration_s % 60)
        msg += f" ({mins}m {secs}s)" if mins else f" ({secs}s)"
    msg += f"\n<i>{datetime.now().strftime('%H:%M:%S')}</i>"
    if output:
        msg += f"\n\n<code>{output[-500:]}</code>"
    return _send(msg)


def notify_task_failed(task_name: str, error: str = "", exit_code: int = 1) -> bool:
    """Call this when a background task fails."""
    msg = (
        f"❌ <b>Task FAILED</b>: {task_name}\n"
        f"Exit code: {exit_code}\n"
        f"<i>{datetime.now().strftime('%H:%M:%S')}</i>"
    )
    if error:
        msg += f"\n\nError:\n<code>{error[-400:]}</code>"
    return _send(msg)


def notify_bot_crash(bot_name: str, log_tail: str = "") -> bool:
    """Call this when a bot process dies unexpectedly."""
    msg = (
        f"⚠️ <b>{bot_name} CRASHED</b>\n"
        f"<i>{datetime.now().strftime('%H:%M:%S')}</i>\n\n"
        f"Heartbeat will attempt auto-restart."
    )
    if log_tail:
        msg += f"\n\nLast log:\n<code>{log_tail[-300:]}</code>"
    return _send(msg)


def notify_bot_restarted(bot_name: str, pid: int = 0) -> bool:
    """Call this when a bot is successfully restarted."""
    msg = f"✅ <b>{bot_name} restarted</b>"
    if pid:
        msg += f" (PID {pid})"
    msg += f"\n<i>{datetime.now().strftime('%H:%M:%S')}</i>"
    return _send(msg)


def notify_daily_stop(balance_gbp: float, loss_gbp: float) -> bool:
    """Call this when the trading bot hits its daily loss limit."""
    return _send(
        f"🛑 <b>Daily loss limit hit</b>\n"
        f"Balance: £{balance_gbp:.2f}\n"
        f"Day loss: -£{abs(loss_gbp):.2f}\n"
        f"Bot paused until tomorrow.\n"
        f"<i>{datetime.now().strftime('%H:%M:%S')}</i>"
    )


def notify_trade(strategy: str, market: str, size_gbp: float, price: float, reason: str = "") -> bool:
    """Call this when a trade is placed."""
    msg = (
        f"💰 <b>Trade placed</b>: {strategy}\n"
        f"Market: {market[:60]}\n"
        f"Size: £{size_gbp:.2f} @ {price:.3f}\n"
    )
    if reason:
        msg += f"Reason: {reason[:100]}\n"
    msg += f"<i>{datetime.now().strftime('%H:%M:%S')}</i>"
    return _send(msg)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Push a Telegram message from the VPS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python telegram_push/push.py "Hello from VPS"
  python telegram_push/push.py --task-done "Scrape Jobs" --output "47 found"
  python telegram_push/push.py --task-fail "Scrape Jobs" --error "Timeout"
  python telegram_push/push.py --crash "polymarket bot"
  python telegram_push/push.py --test
        """
    )
    parser.add_argument("message",      nargs="?", help="Plain message to send")
    parser.add_argument("--task-done",  metavar="NAME", help="Notify task completed")
    parser.add_argument("--task-fail",  metavar="NAME", help="Notify task failed")
    parser.add_argument("--task-start", metavar="NAME", help="Notify task started")
    parser.add_argument("--crash",      metavar="BOT",  help="Notify bot crashed")
    parser.add_argument("--output",     default="",     help="Output/result text")
    parser.add_argument("--error",      default="",     help="Error message")
    parser.add_argument("--cmd",        default="",     help="Command that was run")
    parser.add_argument("--test",       action="store_true", help="Send test message")

    args = parser.parse_args()

    if args.test:
        ok = notify(
            f"🧪 <b>Telegram push test</b>\n"
            f"VPS → Your phone\n"
            f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>\n"
            f"If you see this, proactive notifications are working ✅"
        )
        print("✅ Test message sent!" if ok else "❌ Failed — check TELEGRAM_BOT_TOKEN and TELEGRAM_USER_ID in .env")
        return

    if args.task_done:
        notify_task_done(args.task_done, output=args.output)
    elif args.task_fail:
        notify_task_failed(args.task_fail, error=args.error)
    elif args.task_start:
        notify_task_start(args.task_start, cmd=args.cmd)
    elif args.crash:
        notify_bot_crash(args.crash, log_tail=args.output)
    elif args.message:
        notify(args.message)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
