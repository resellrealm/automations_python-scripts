"""
Config loader for Apprenticeship Applier.
Reads from .env file in the same directory.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

_env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_env_path)


class Config:
    # Kimi AI
    AI_API_URL: str = os.getenv("AI_API_URL", "https://api.moonshot.cn/v1/chat/completions")
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "moonshot-v1-8k")

    # Search
    SEARCH_KEYWORDS: list = [k.strip() for k in os.getenv("SEARCH_KEYWORDS", "software,IT").split(",")]
    SEARCH_LOCATION: str = os.getenv("SEARCH_LOCATION", "London")
    SEARCH_DISTANCE_MILES: int = int(os.getenv("SEARCH_DISTANCE_MILES", "30"))
    SEARCH_LEVELS: list = [
        l.strip() for l in os.getenv("SEARCH_LEVELS", "").split(",") if l.strip()
    ]

    # Application
    MAX_APPLICATIONS_PER_RUN: int = int(os.getenv("MAX_APPLICATIONS_PER_RUN", "10"))
    DRY_RUN: bool = os.getenv("DRY_RUN", "false").lower() == "true"
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() == "true"

    # gov.uk account
    GOVUK_EMAIL: str    = os.getenv("GOVUK_EMAIL", "")
    GOVUK_PASSWORD: str = os.getenv("GOVUK_PASSWORD", "")

    # Telegram bot
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str   = os.getenv("TELEGRAM_CHAT_ID", "")

    # CAPTCHA solving
    TWOCAPTCHA_API_KEY: str = os.getenv("TWOCAPTCHA_API_KEY", "")  # optional, ~$3/1000 solves
    VPS_IP: str             = os.getenv("VPS_IP", "")              # your VPS public IP for noVNC

    # Paths
    BASE_DIR: Path = Path(__file__).parent
    DB_PATH: str = str(BASE_DIR / "applications.db")
    PROFILE_FILE: str = str(BASE_DIR / "user_profile.json")
    COVER_LETTERS_DIR: str = str(BASE_DIR / "cover_letters")
    SCREENSHOTS_DIR: str = str(BASE_DIR / "screenshots")

    # Gov.uk apprenticeship search URL
    SEARCH_BASE_URL: str = "https://www.findapprenticeship.service.gov.uk"

    @classmethod
    def validate(cls):
        missing = []
        if not cls.AI_API_KEY:
            missing.append("AI_API_KEY")
        if not cls.GOVUK_EMAIL:
            missing.append("GOVUK_EMAIL")
        if not cls.GOVUK_PASSWORD:
            missing.append("GOVUK_PASSWORD")
        if not Path(cls.PROFILE_FILE).exists():
            missing.append(f"user_profile.json (expected at {cls.PROFILE_FILE})")
        if not cls.TELEGRAM_BOT_TOKEN:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not cls.TELEGRAM_CHAT_ID:
            missing.append("TELEGRAM_CHAT_ID")
        if missing:
            raise EnvironmentError(
                f"Missing required config: {', '.join(missing)}\n"
                f"Copy .env.example to .env and fill in your values.\n"
                f"Also fill in user_profile.json with your personal details."
            )
