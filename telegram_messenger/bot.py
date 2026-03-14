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
    "That's it. No other commands."
)


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
