"""Config loader for OpenClaw Telegram bot."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load root .env first, then telegram_messenger/.env on top (local overrides root)
_root = Path(__file__).parent.parent
load_dotenv(_root / ".env")
load_dotenv(Path(__file__).parent / ".env", override=True)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_USER_ID   = int(os.getenv("TELEGRAM_USER_ID", "0"))

# Kimi / Moonshot — real API, not a local VPS server
AI_API_URL = os.getenv("AI_API_URL", "https://api.moonshot.cn/v1")
AI_API_KEY = os.getenv("AI_API_KEY", "") or os.getenv("KIMI_API_KEY", "")
KIMI_MODEL = os.getenv("KIMI_MODEL", "moonshot-v1-8k")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")
if not TELEGRAM_USER_ID:
    raise ValueError("TELEGRAM_USER_ID not set in .env")
