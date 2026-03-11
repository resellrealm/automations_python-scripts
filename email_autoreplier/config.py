"""Config for Email Auto-Replier (Zoho Mail)."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")


class Config:
    # Zoho Mail
    ZOHO_EMAIL: str       = os.getenv("ZOHO_EMAIL", "")
    ZOHO_APP_PASSWORD: str = os.getenv("ZOHO_APP_PASSWORD", "")
    ZOHO_IMAP_HOST: str   = os.getenv("ZOHO_IMAP_HOST", "imappro.zoho.eu")
    ZOHO_IMAP_PORT: int   = int(os.getenv("ZOHO_IMAP_PORT", "993"))
    ZOHO_SMTP_HOST: str   = os.getenv("ZOHO_SMTP_HOST", "smtppro.zoho.eu")
    ZOHO_SMTP_PORT: int   = int(os.getenv("ZOHO_SMTP_PORT", "587"))

    # Kimi AI
    AI_API_URL: str  = os.getenv("AI_API_URL", "https://api.moonshot.cn/v1/chat/completions")
    AI_API_KEY: str  = os.getenv("AI_API_KEY", "")
    AI_MODEL: str    = os.getenv("AI_MODEL", "moonshot-v1-8k")

    # Identity
    YOUR_NAME: str   = os.getenv("YOUR_NAME", "The Team")
    YOUR_ROLE: str   = os.getenv("YOUR_ROLE", "Assistant")
    REPLY_TONE: str  = os.getenv("REPLY_TONE", "professional and friendly")

    # Polling
    POLL_INTERVAL_MINUTES: int  = int(os.getenv("POLL_INTERVAL_MINUTES", "5"))
    MAX_EMAILS_PER_CYCLE: int   = int(os.getenv("MAX_EMAILS_PER_CYCLE", "20"))

    # Paths
    DB_PATH: str           = str(Path(__file__).parent / "emails.db")
    ESCALATION_FILE: str   = str(Path(__file__).parent / "escalation_queue.json")

    @classmethod
    def validate(cls):
        missing = [k for k, v in {
            "ZOHO_EMAIL": cls.ZOHO_EMAIL,
            "ZOHO_APP_PASSWORD": cls.ZOHO_APP_PASSWORD,
            "AI_API_KEY": cls.AI_API_KEY,
        }.items() if not v]
        if missing:
            raise EnvironmentError(
                f"Missing required .env values: {', '.join(missing)}\n"
                f"Edit email_autoreplier/.env and fill them in."
            )
