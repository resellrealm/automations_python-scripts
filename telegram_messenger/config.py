"""Config loader for OpenClaw Telegram bot."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_USER_ID   = int(os.getenv("TELEGRAM_USER_ID", "0"))   # your numeric Telegram ID
AI_API_URL         = os.getenv("AI_API_URL", "")               # Kimi VPS endpoint (base URL, no /chat/completions)
AI_API_KEY         = os.getenv("AI_API_KEY", "")
KIMI_MODEL         = os.getenv("KIMI_MODEL", "moonshot-v1-8k")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")
if not TELEGRAM_USER_ID:
    raise ValueError("TELEGRAM_USER_ID not set in .env")
