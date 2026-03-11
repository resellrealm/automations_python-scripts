"""
Zoho Mail Client
Handles all email operations via IMAP (reading) and SMTP (sending).
Uses app-specific password — no OAuth, works straight on VPS.

Libraries used:
  imap-tools — cleaner IMAP wrapper (pip install imap-tools)
  smtplib    — stdlib SMTP for sending
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

from imap_tools import MailBox, AND, MailMessage

from config import Config
from shared.logger import get_logger

logger = get_logger("zoho_client")


class ZohoClient:
    def __init__(self):
        self._test_connection()

    def _test_connection(self):
        """Quick connection test on startup."""
        try:
            with MailBox(Config.ZOHO_IMAP_HOST, Config.ZOHO_IMAP_PORT).login(
                Config.ZOHO_EMAIL, Config.ZOHO_APP_PASSWORD
            ):
                logger.info(f"Zoho Mail connected — {Config.ZOHO_EMAIL}")
        except Exception as e:
            raise ConnectionError(
                f"Could not connect to Zoho IMAP ({Config.ZOHO_IMAP_HOST}): {e}\n"
                f"Check ZOHO_EMAIL, ZOHO_APP_PASSWORD, and ZOHO_IMAP_HOST in .env"
            )

    def get_unread_emails(self, limit: int = None) -> List[dict]:
        """
        Fetch unread emails from the inbox.
        Returns list of dicts ready for the AI handler.
        """
        limit = limit or Config.MAX_EMAILS_PER_CYCLE
        emails = []

        try:
            with MailBox(Config.ZOHO_IMAP_HOST, Config.ZOHO_IMAP_PORT).login(
                Config.ZOHO_EMAIL, Config.ZOHO_APP_PASSWORD
            ) as mailbox:
                # Fetch unseen, newest first, up to limit
                msgs = list(mailbox.fetch(
                    criteria=AND(seen=False),
                    mark_seen=False,   # don't mark yet — we do that after processing
                    limit=limit,
                    reverse=True,
                ))

            for msg in msgs:
                emails.append(self._parse(msg))

            logger.info(f"Fetched {len(emails)} unread email(s).")

        except Exception as e:
            logger.error(f"Failed to fetch emails: {e}")

        return emails

    def get_thread_context(self, subject: str, sender: str) -> str:
        """
        Fetch the 3 most recent messages in the same thread (matched by subject).
        Used to give the AI conversation history.
        """
        try:
            # Strip Re:/Fwd: prefixes for matching
            clean_subject = subject.replace("Re: ", "").replace("Fwd: ", "").strip()

            with MailBox(Config.ZOHO_IMAP_HOST, Config.ZOHO_IMAP_PORT).login(
                Config.ZOHO_EMAIL, Config.ZOHO_APP_PASSWORD
            ) as mailbox:
                msgs = list(mailbox.fetch(
                    criteria=AND(subject=clean_subject),
                    mark_seen=False,
                    limit=3,
                    reverse=True,
                ))

            parts = []
            for msg in msgs:
                body = (msg.text or msg.html or "")[:400]
                parts.append(f"From: {msg.from_}\nDate: {msg.date}\n{body}")

            return "\n\n---\n\n".join(parts)

        except Exception as e:
            logger.debug(f"Could not fetch thread context: {e}")
            return ""

    def send_reply(self, to: str, subject: str, body: str, reply_to_uid: str = None):
        """Send a reply via Zoho SMTP (TLS on port 587)."""
        msg = MIMEMultipart()
        msg["From"]    = Config.ZOHO_EMAIL
        msg["To"]      = to
        msg["Subject"] = subject if subject.startswith("Re:") else f"Re: {subject}"
        msg.attach(MIMEText(body, "plain", "utf-8"))

        try:
            with smtplib.SMTP(Config.ZOHO_SMTP_HOST, Config.ZOHO_SMTP_PORT) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.login(Config.ZOHO_EMAIL, Config.ZOHO_APP_PASSWORD)
                server.sendmail(Config.ZOHO_EMAIL, to, msg.as_string())

            logger.info(f"Reply sent → {to} | Subject: {subject}")

        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            raise

    def mark_as_read(self, uid: str):
        """Mark a message as seen by UID."""
        try:
            with MailBox(Config.ZOHO_IMAP_HOST, Config.ZOHO_IMAP_PORT).login(
                Config.ZOHO_EMAIL, Config.ZOHO_APP_PASSWORD
            ) as mailbox:
                mailbox.flag([uid], r"\Seen", True)
        except Exception as e:
            logger.warning(f"Could not mark UID {uid} as read: {e}")

    def move_to_folder(self, uid: str, folder: str):
        """Move a message to a folder (creates it if needed)."""
        try:
            with MailBox(Config.ZOHO_IMAP_HOST, Config.ZOHO_IMAP_PORT).login(
                Config.ZOHO_EMAIL, Config.ZOHO_APP_PASSWORD
            ) as mailbox:
                # Create folder if it doesn't exist
                existing = [f.name for f in mailbox.folder.list()]
                if folder not in existing:
                    mailbox.folder.create(folder)
                mailbox.move([uid], folder)
        except Exception as e:
            logger.warning(f"Could not move UID {uid} to '{folder}': {e}")

    @staticmethod
    def _parse(msg: MailMessage) -> dict:
        """Convert imap-tools MailMessage to our standard email dict."""
        body = msg.text or ""
        if not body and msg.html:
            # Strip basic HTML tags if no plain text
            import re
            body = re.sub(r"<[^>]+>", " ", msg.html)

        return {
            "message_id": msg.uid,          # use UID as ID
            "uid":        msg.uid,
            "thread_id":  msg.uid,          # Zoho IMAP doesn't expose thread IDs
            "sender":     msg.from_,
            "subject":    msg.subject or "(no subject)",
            "body":       body.strip(),
            "received_at": str(msg.date),
            "snippet":    body.strip()[:200],
        }
