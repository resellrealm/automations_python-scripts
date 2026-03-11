"""
Config loader for Email Auto-Replier.
Reads from .env file in the same directory.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the same directory as this file
_env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_env_path)


class Config:
    # Kimi AI
    AI_API_URL: str = os.getenv("AI_API_URL", "https://api.moonshot.cn/v1/chat/completions")
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "moonshot-v1-8k")

    # Gmail OAuth2
    GMAIL_CLIENT_ID: str = os.getenv("GMAIL_CLIENT_ID", "")
    GMAIL_CLIENT_SECRET: str = os.getenv("GMAIL_CLIENT_SECRET", "")

    # Token storage path (saved after first OAuth consent)
    TOKEN_FILE: str = str(Path(__file__).parent / "token.json")
    CREDENTIALS_FILE: str = str(Path(__file__).parent / "credentials.json")

    # Identity
    YOUR_NAME: str = os.getenv("YOUR_NAME", "The Team")
    YOUR_EMAIL: str = os.getenv("YOUR_EMAIL", "")
    YOUR_ROLE: str = os.getenv("YOUR_ROLE", "Assistant")
    REPLY_TONE: str = os.getenv("REPLY_TONE", "professional and friendly")

    # Polling
    POLL_INTERVAL_MINUTES: int = int(os.getenv("POLL_INTERVAL_MINUTES", "5"))
    MAX_EMAILS_PER_CYCLE: int = int(os.getenv("MAX_EMAILS_PER_CYCLE", "20"))

    # Database
    DB_PATH: str = str(Path(__file__).parent / "emails.db")

    # Escalation queue
    ESCALATION_FILE: str = str(Path(__file__).parent / "escalation_queue.json")

    # Gmail scopes needed
    GMAIL_SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.modify",
    ]

    @classmethod
    def validate(cls):
        missing = []
        if not cls.AI_API_KEY:
            missing.append("AI_API_KEY")
        if not cls.GMAIL_CLIENT_ID:
            missing.append("GMAIL_CLIENT_ID")
        if not cls.GMAIL_CLIENT_SECRET:
            missing.append("GMAIL_CLIENT_SECRET")
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Copy .env.example to .env and fill in your values."
            )
