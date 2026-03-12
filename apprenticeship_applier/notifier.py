"""
Telegram Notifier — send messages, photos, and wait for replies.
Uses the Telegram Bot API directly (no async framework needed).

Usage:
    notifier.send("Application submitted to KPMG!")
    code = notifier.ask("Enter your 2FA code:")
    notifier.send_photo("screenshot.png", caption="CAPTCHA - solve and reply 'done'")
"""

import time
import requests
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        self.token   = token
        self.chat_id = str(chat_id)
        self.base    = f"https://api.telegram.org/bot{token}"
        self._offset = None  # for getUpdates polling

    def send(self, text: str) -> bool:
        """Send a text message."""
        try:
            r = requests.post(
                f"{self.base}/sendMessage",
                json={"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"},
                timeout=10,
            )
            return r.ok
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False

    def send_photo(self, path: str, caption: str = "") -> bool:
        """Send a photo file."""
        try:
            with open(path, "rb") as f:
                r = requests.post(
                    f"{self.base}/sendPhoto",
                    data={"chat_id": self.chat_id, "caption": caption},
                    files={"photo": f},
                    timeout=20,
                )
            return r.ok
        except Exception as e:
            logger.error(f"Telegram send_photo failed: {e}")
            return False

    def wait_for_reply(self, timeout: int = 300, prompt: str = "") -> str:
        """
        Block until the user sends a reply in Telegram.
        Returns the message text, or "" on timeout.
        """
        if prompt:
            self.send(prompt)

        deadline = time.time() + timeout
        logger.info(f"Waiting for Telegram reply (timeout={timeout}s)...")

        while time.time() < deadline:
            try:
                params = {"timeout": 20, "allowed_updates": ["message"]}
                if self._offset is not None:
                    params["offset"] = self._offset

                r = requests.get(
                    f"{self.base}/getUpdates",
                    params=params,
                    timeout=25,
                )
                if not r.ok:
                    time.sleep(2)
                    continue

                updates = r.json().get("result", [])
                for update in updates:
                    self._offset = update["update_id"] + 1
                    msg = update.get("message", {})
                    if str(msg.get("chat", {}).get("id", "")) == self.chat_id:
                        text = msg.get("text", "").strip()
                        logger.info(f"Got Telegram reply: {text}")
                        return text

            except Exception as e:
                logger.debug(f"getUpdates error: {e}")
                time.sleep(3)

        logger.warning("Telegram reply timed out.")
        self.send("⏰ Timed out waiting for your reply — skipping this step.")
        return ""

    def ask(self, question: str, timeout: int = 300) -> str:
        """Send a question and wait for the user's reply."""
        return self.wait_for_reply(timeout=timeout, prompt=question)


# ── Singleton (initialised lazily from config) ────────────────────
_notifier = None

def get_notifier() -> TelegramNotifier:
    global _notifier
    if _notifier is None:
        from config import Config
        if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
            raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env")
        _notifier = TelegramNotifier(Config.TELEGRAM_BOT_TOKEN, Config.TELEGRAM_CHAT_ID)
    return _notifier
