"""
OpenClaw — Telegram Messenger Bot
===================================
Pure relay. No commands, no state, no logic.

Any message from the authorized user:
  - Starts with /kimi → sent to Kimi AI (fast/cheap)
  - Everything else  → sent to Claude CLI (claude -p "...")

Replies arrive as plain text and are forwarded back to Telegram.

Setup:
  1. Create bot via @BotFather → copy token to .env
  2. Get your Telegram user ID from @userinfobot → copy to .env
  3. pip install python-telegram-bot requests python-dotenv
  4. python bot.py

Run as daemon on VPS:
  nohup python bot.py >> openclaw.log 2>&1 &
"""

import logging
import subprocess
import requests as req
from pathlib import Path

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_USER_ID, AI_API_URL, AI_API_KEY, KIMI_MODEL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("openclaw.log")],
)
logger = logging.getLogger(__name__)

HELP_TEXT = (
    "🤖 <b>OpenClaw Messenger</b>\n\n"
    "Send any message → Claude answers\n"
    "Start with <code>/kimi</code> → Kimi AI answers\n\n"
    "<b>Quick shortcuts:</b>\n"
    "  <code>done?</code> or <code>is it done</code> → task status\n"
    "  <code>status</code> → all bots + tasks health\n"
    "  <code>balance</code> → Polymarket P&amp;L\n\n"
    "That's it. No other commands."
)

# Phrases that mean "check task status"
TASK_STATUS_PHRASES = {
    "done?", "is it done", "is it done?", "done yet", "done yet?",
    "finished?", "finished yet", "are you done", "are you done?",
    "is the task done", "task done?", "task status", "what's the status",
    "whats the status", "still running?", "still going?",
}

# Phrases that mean "check all bots"
STATUS_PHRASES = {"status", "bot status", "all bots", "health", "health check"}

# Phrases that mean "show P&L"
BALANCE_PHRASES = {"balance", "pnl", "p&l", "how much", "profit", "money", "earnings"}


def _quick_task_status() -> str:
    """Read tasks.json and return a quick status string."""
    tasks_file = Path(__file__).parent.parent / "vps_tasks" / "tasks.json"
    if not tasks_file.exists():
        return "📭 No background tasks recorded."
    try:
        import json
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


# ── AI backends ───────────────────────────────────────────────────────────────

def ask_claude(message: str) -> str:
    """Route message to Claude CLI and return response."""
    try:
        result = subprocess.run(
            ["claude", "-p", message],
            capture_output=True,
            text=True,
            timeout=120,
        )
        response = result.stdout.strip()
        if not response and result.stderr:
            response = result.stderr.strip()
        return response or "Claude returned an empty response."
    except FileNotFoundError:
        return "❌ Claude CLI not found. Make sure `claude` is installed and in PATH."
    except subprocess.TimeoutExpired:
        return "❌ Claude timed out (120s)."
    except Exception as e:
        return f"❌ Claude error: {e}"


def ask_kimi(message: str) -> str:
    """Route message to Kimi AI via OpenAI-compatible API."""
    if not AI_API_URL or not AI_API_KEY:
        return "❌ Kimi not configured. Set AI_API_URL and AI_API_KEY in .env"
    try:
        # Build endpoint — handle trailing slash or missing /chat/completions
        base = AI_API_URL.rstrip("/")
        if not base.endswith("/chat/completions"):
            base = base + "/chat/completions"

        resp = req.post(
            base,
            headers={"Authorization": f"Bearer {AI_API_KEY}"},
            json={
                "model":    KIMI_MODEL,
                "messages": [{"role": "user", "content": message}],
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"❌ Kimi error: {e}"


# ── Telegram handlers ─────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Only respond to the authorized user
    if user_id != TELEGRAM_USER_ID:
        logger.warning(f"Unauthorized access attempt from user_id={user_id}")
        await update.message.reply_text("❌ Not authorized.")
        return

    text = (update.message.text or "").strip()
    if not text:
        return

    # /help
    if text.lower() in ("/help", "/start"):
        await update.message.reply_html(HELP_TEXT)
        return

    # Quick shortcuts — no need to go to Claude
    text_lower = text.lower().strip("?! ")
    if text_lower in TASK_STATUS_PHRASES or "done" in text_lower and len(text) < 30:
        await update.message.reply_html(_quick_task_status())
        return

    if text_lower in STATUS_PHRASES:
        result = subprocess.run(
            ["python", "vps_tasks/task_runner.py", "--status"],
            capture_output=True, text=True, cwd=str(Path(__file__).parent.parent)
        )
        reply = result.stdout.strip() or "No task data."
        await update.message.reply_html(reply or "No tasks running.")
        return

    # Route
    if text.lower().startswith("/kimi"):
        query = text[5:].strip() or "hello"
        logger.info(f"→ Kimi: {query[:80]}")
        await update.message.reply_text("⏳ Asking Kimi...")
        response = ask_kimi(query)
    else:
        logger.info(f"→ Claude: {text[:80]}")
        await update.message.reply_text("⏳ Asking Claude...")
        response = ask_claude(text)

    # Telegram has a 4096 char limit — split if needed
    if len(response) <= 4096:
        await update.message.reply_text(response)
    else:
        for i in range(0, len(response), 4096):
            await update.message.reply_text(response[i:i+4096])


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    logger.info(f"OpenClaw starting — authorized user_id={TELEGRAM_USER_ID}")
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    logger.info("Polling for messages...")
    app.run_polling()


if __name__ == "__main__":
    main()
