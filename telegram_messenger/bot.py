"""
OpenClaw — VPS Command Bot
===========================
Messages you send → real actions on the VPS.

Commands:
  status          → show all running bots + recent tasks
  scan            → run one Polymarket market scan (background, texts you when done)
  apply           → run apprenticeship applier (background, texts you when done)
  balance / p&l   → show Polymarket P&L
  logs [bot]      → tail the last 30 lines of a bot log
  start bots      → start all bots via heartbeat
  stop bots       → stop all bots
  done? / is it done? → check background task status
  /kimi <msg>     → send to Kimi AI (fast, cheap)
  anything else   → send to Claude CLI

Run on VPS:
    nohup python telegram_messenger/bot.py >> openclaw.log 2>&1 &
"""

import json
import logging
import subprocess
from pathlib import Path

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("openclaw.log")],
)
logger = logging.getLogger(__name__)

PROJECT = Path(__file__).parent.parent

HELP_TEXT = (
    "🤖 <b>OpenClaw — VPS Control</b>\n\n"
    "<b>Bot commands:</b>\n"
    "  <code>status</code>       — all bots + task status\n"
    "  <code>scan</code>         — run Polymarket scan now\n"
    "  <code>apply</code>        — run apprenticeship applier\n"
    "  <code>balance</code>      — Polymarket P&amp;L\n"
    "  <code>logs</code>         — show recent bot logs\n"
    "  <code>logs poly</code>    — Polymarket log\n"
    "  <code>logs kalshi</code>  — Kalshi log\n"
    "  <code>start bots</code>   — start all trading bots\n"
    "  <code>stop bots</code>    — stop all trading bots\n"
    "  <code>done?</code>        — check if background task finished\n\n"
    "<b>AI:</b>\n"
    "  <code>/kimi msg</code>    — ask Kimi AI\n"
    "  <code>anything else</code>— ask Claude\n"
)

# ── Quick phrase matchers ─────────────────────────────────────────────────────

TASK_STATUS_PHRASES = {
    "done?", "is it done", "is it done?", "done yet", "done yet?",
    "finished?", "finished yet", "are you done", "are you done?",
    "is the task done", "task done?", "task status", "what's the status",
    "whats the status", "still running?", "still going?",
}
STATUS_PHRASES   = {"status", "bot status", "all bots", "health", "health check"}
BALANCE_PHRASES  = {"balance", "pnl", "p&l", "how much", "profit", "money", "earnings"}
SCAN_PHRASES     = {"scan", "scan markets", "scan now", "run scan", "check markets"}
APPLY_PHRASES    = {"apply", "apply jobs", "apply now", "run apply", "apprenticeship"}
LOGS_PHRASES     = {"logs", "log", "show logs", "recent logs"}
START_PHRASES    = {"start bots", "start all", "start trading", "launch bots"}
STOP_PHRASES     = {"stop bots", "stop all", "stop trading", "kill bots"}


# ── VPS helpers ───────────────────────────────────────────────────────────────

def _run(cmd: list, cwd=None, timeout=10) -> str:
    """Run a shell command, return stdout+stderr combined."""
    try:
        r = subprocess.run(
            cmd, cwd=cwd or PROJECT,
            capture_output=True, text=True, timeout=timeout,
        )
        return (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return "[timed out]"
    except Exception as e:
        return f"[error: {e}]"


def _background_task(name: str, cmd: str) -> str:
    """Start a task via task_runner (background, texts when done)."""
    import os
    runner = PROJECT / "vps_tasks" / "task_runner.py"
    log    = PROJECT / "vps_tasks" / f"{name.replace(' ', '_')}.log"
    try:
        subprocess.Popen(
            ["python", str(runner), "--name", name, "--cmd", cmd],
            cwd=str(PROJECT),
            stdout=open(log, "a"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        return f"⏳ <b>{name}</b> started in background.\nI'll text you when it's done."
    except Exception as e:
        return f"❌ Failed to start {name}: {e}"


def _quick_task_status() -> str:
    tasks_file = PROJECT / "vps_tasks" / "tasks.json"
    if not tasks_file.exists():
        return "📭 No background tasks recorded."
    try:
        tasks = json.loads(tasks_file.read_text())
        if not tasks:
            return "📭 No background tasks recorded."
        lines = []
        for t in sorted(tasks.values(), key=lambda x: x.get("started", ""), reverse=True)[:5]:
            icon = {"running": "⏳", "done": "✅", "failed": "❌"}.get(t.get("status"), "❓")
            name = t.get("name", "task")
            fin  = t.get("finished", "")[:16].replace("T", " ")
            tail = t.get("output_tail", "")[-200:]
            line = f"{icon} <b>{name}</b> — {t.get('status')}"
            if fin:
                line += f" at {fin}"
            if tail and t.get("status") in ("done", "failed"):
                line += f"\n<code>{tail}</code>"
            lines.append(line)
        return "\n\n".join(lines)
    except Exception as e:
        return f"❌ Could not read task status: {e}"


def _full_status() -> str:
    """Show running processes + recent tasks."""
    lines = ["📊 <b>VPS Status</b>\n"]

    # Check which bots are running via pgrep
    bots = {
        "Polymarket": "polymarket_flipper/main.py",
        "Kalshi":     "kalshi_flipper/main.py",
        "Oddpool":    "oddpool/main.py",
        "Heartbeat":  "heartbeat.py",
        "OpenClaw":   "telegram_messenger/bot.py",
    }
    bot_lines = []
    for name, pattern in bots.items():
        r = subprocess.run(["pgrep", "-f", pattern], capture_output=True)
        icon = "🟢" if r.returncode == 0 else "🔴"
        bot_lines.append(f"  {icon} {name}")
    lines.append("<b>Bots:</b>\n" + "\n".join(bot_lines))

    # Recent tasks
    task_status = _quick_task_status()
    if "No background" not in task_status:
        lines.append("\n<b>Recent tasks:</b>\n" + task_status)

    return "\n".join(lines)


def _tail_log(bot_name: str = "") -> str:
    """Tail last 30 lines of a bot log."""
    logs = {
        "poly":    PROJECT / "polymarket_flipper" / "bot.log",
        "kalshi":  PROJECT / "kalshi_flipper" / "bot.log",
        "oddpool": PROJECT / "oddpool" / "bot.log",
        "heart":   PROJECT / "heartbeat.log",
        "openclaw":PROJECT / "telegram_messenger" / "openclaw.log",
    }
    bot_name = bot_name.lower().strip()
    # match partial name
    matched = None
    for key, path in logs.items():
        if key in bot_name or bot_name in key:
            matched = path
            break
    if not matched:
        # default: polymarket
        matched = logs["poly"]

    if not matched.exists():
        return f"❌ Log not found: {matched.name}"

    lines = matched.read_text(errors="ignore").splitlines()[-30:]
    return f"<code>{'chr(10)'.join(lines)}</code>" if lines else "Log is empty."


def _polymarket_balance() -> str:
    """Read today's P&L from trade logger."""
    try:
        r = _run(
            ["python", "-c",
             "from polymarket_flipper.trade_logger import get_daily_summary; "
             "import json; print(json.dumps(get_daily_summary()))"],
            timeout=15,
        )
        data = json.loads(r)
        pnl  = data.get("pnl_gbp", 0)
        trades = data.get("trades_closed", 0)
        return (
            f"💰 <b>Today's P&amp;L</b>\n"
            f"PnL: £{pnl:+.2f}\n"
            f"Trades closed: {trades}"
        )
    except Exception:
        # Fallback: read bankroll
        try:
            bf = PROJECT / "polymarket_flipper" / "bankroll.json"
            if bf.exists():
                data = json.loads(bf.read_text())
                bal = data.get("balance_gbp", "?")
                return f"💰 <b>Bankroll</b>: £{bal}"
        except Exception:
            pass
        return "❌ Could not fetch balance."


# ── AI backends ───────────────────────────────────────────────────────────────

KIMI_CLI = PROJECT / "kimi_cli.py"


def _run_ai(cmd: list, timeout: int = 120) -> str:
    """Run an AI CLI command, return its stdout."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, cwd=str(PROJECT),
        )
        response = result.stdout.strip()
        if not response and result.stderr:
            response = result.stderr.strip()
        return response or "(empty response)"
    except subprocess.TimeoutExpired:
        return f"❌ Timed out ({timeout}s)."
    except FileNotFoundError:
        return f"❌ Command not found: {cmd[0]}"
    except Exception as e:
        return f"❌ Error: {e}"


def ask_claude(message: str) -> str:
    """Send message to Claude CLI (`claude -p`)."""
    return _run_ai(["claude", "-p", message, "--output-format", "text"])


def ask_kimi(message: str) -> str:
    """Send message to Kimi CLI (`python kimi_cli.py`)."""
    return _run_ai(["python", str(KIMI_CLI), message])


# ── Telegram handler ──────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != TELEGRAM_USER_ID:
        logger.warning(f"Unauthorized: user_id={user_id}")
        await update.message.reply_text("❌ Not authorized.")
        return

    text = (update.message.text or "").strip()
    if not text:
        return

    tl = text.lower().strip("?! ")

    # ── /help or /start ──────────────────────────────────────
    if tl in ("/help", "/start", "help"):
        await update.message.reply_html(HELP_TEXT)
        return

    # ── Task status: "done?" ─────────────────────────────────
    if tl in TASK_STATUS_PHRASES or ("done" in tl and len(text) < 30):
        await update.message.reply_html(_quick_task_status())
        return

    # ── Full VPS status ──────────────────────────────────────
    if tl in STATUS_PHRASES:
        await update.message.reply_html(_full_status())
        return

    # ── Balance / P&L ────────────────────────────────────────
    if tl in BALANCE_PHRASES:
        await update.message.reply_html(_polymarket_balance())
        return

    # ── Scan markets (background task) ───────────────────────
    if tl in SCAN_PHRASES:
        reply = _background_task(
            "Market Scan",
            "python polymarket_flipper/main.py --dry-run --once",
        )
        await update.message.reply_html(reply)
        return

    # ── Run apprenticeship applier (background task) ─────────
    if tl in APPLY_PHRASES:
        reply = _background_task(
            "Apply Jobs",
            "python apprenticeship_applier/main.py --apply --limit 5",
        )
        await update.message.reply_html(reply)
        return

    # ── Tail logs ────────────────────────────────────────────
    if any(p in tl for p in LOGS_PHRASES):
        # e.g. "logs poly" → tail polymarket log
        suffix = tl.replace("logs", "").replace("log", "").strip()
        await update.message.reply_html(_tail_log(suffix))
        return

    # ── Start bots ───────────────────────────────────────────
    if tl in START_PHRASES:
        reply = _background_task(
            "Start Bots",
            "python claude_agents/heartbeat.py",
        )
        await update.message.reply_html(reply)
        return

    # ── Stop bots ────────────────────────────────────────────
    if tl in STOP_PHRASES:
        out = _run(["pkill", "-f", "polymarket_flipper/main.py"])
        _run(["pkill", "-f", "kalshi_flipper/main.py"])
        _run(["pkill", "-f", "oddpool/main.py"])
        await update.message.reply_html("🛑 <b>All trading bots stopped.</b>")
        return

    # ── /kimi → Kimi AI ──────────────────────────────────────
    if text.lower().startswith("/kimi"):
        query = text[5:].strip() or "hello"
        logger.info(f"→ Kimi: {query[:80]}")
        await update.message.reply_text("⏳ Asking Kimi...")
        response = ask_kimi(query)

    # ── Everything else → Claude CLI ─────────────────────────
    else:
        logger.info(f"→ Claude: {text[:80]}")
        await update.message.reply_text("⏳ Asking Claude...")
        response = ask_claude(text)

    # Split long responses (Telegram 4096 char limit)
    for i in range(0, max(len(response), 1), 4096):
        await update.message.reply_text(response[i:i + 4096])


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    logger.info(f"OpenClaw starting — authorized user_id={TELEGRAM_USER_ID}")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    logger.info("Polling for messages...")
    app.run_polling()


if __name__ == "__main__":
    main()
