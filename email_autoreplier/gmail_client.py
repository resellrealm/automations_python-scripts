"""
Gmail Client
Handles OAuth2 authentication and all Gmail API operations.

FIRST RUN SETUP:
    1. Go to Google Cloud Console → APIs & Services → Credentials
    2. Create an OAuth 2.0 Client ID (Desktop App)
    3. Download the JSON and save it as credentials.json in this folder
    4. Run main.py once — it will open a browser for you to log in
    5. After login, token.json is saved and used for all future runs
"""

import base64
import email as email_lib
import os
from pathlib import Path
from typing import List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import Config
from shared.logger import get_logger

logger = get_logger("gmail_client")


class GmailClient:
    def __init__(self):
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Run OAuth2 flow — opens browser on first run, uses saved token after."""
        creds = None

        if Path(Config.TOKEN_FILE).exists():
            creds = Credentials.from_authorized_user_file(Config.TOKEN_FILE, Config.GMAIL_SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired Gmail token...")
                creds.refresh(Request())
            else:
                logger.info("Starting Gmail OAuth2 flow — browser will open...")
                if not Path(Config.CREDENTIALS_FILE).exists():
                    # Build credentials.json from env vars
                    import json
                    cred_data = {
                        "installed": {
                            "client_id": Config.GMAIL_CLIENT_ID,
                            "client_secret": Config.GMAIL_CLIENT_SECRET,
                            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                        }
                    }
                    with open(Config.CREDENTIALS_FILE, "w") as f:
                        json.dump(cred_data, f)

                flow = InstalledAppFlow.from_client_secrets_file(
                    Config.CREDENTIALS_FILE, Config.GMAIL_SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(Config.TOKEN_FILE, "w") as f:
                f.write(creds.to_json())
            logger.info(f"Token saved to {Config.TOKEN_FILE}")

        self.service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail authenticated successfully.")

    def get_unread_emails(self, max_results: int = None) -> List[dict]:
        """
        Fetch unread emails from the inbox.
        Returns list of dicts: {message_id, thread_id, sender, subject, body, received_at, snippet}
        """
        max_results = max_results or Config.MAX_EMAILS_PER_CYCLE
        try:
            result = self.service.users().messages().list(
                userId="me",
                q="is:unread in:inbox",
                maxResults=max_results,
            ).execute()

            messages = result.get("messages", [])
            if not messages:
                return []

            emails = []
            for msg_ref in messages:
                msg = self._get_full_message(msg_ref["id"])
                if msg:
                    emails.append(msg)

            logger.info(f"Fetched {len(emails)} unread email(s).")
            return emails

        except HttpError as e:
            logger.error(f"Failed to fetch emails: {e}")
            return []

    def _get_full_message(self, message_id: str) -> Optional[dict]:
        """Fetch and parse a full email message."""
        try:
            msg = self.service.users().messages().get(
                userId="me", id=message_id, format="full"
            ).execute()

            headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
            subject = headers.get("Subject", "(no subject)")
            sender = headers.get("From", "unknown")
            date = headers.get("Date", "")

            body = self._extract_body(msg["payload"])

            return {
                "message_id": message_id,
                "thread_id": msg["threadId"],
                "sender": sender,
                "subject": subject,
                "body": body,
                "received_at": date,
                "snippet": msg.get("snippet", ""),
            }

        except HttpError as e:
            logger.error(f"Failed to get message {message_id}: {e}")
            return None

    def _extract_body(self, payload: dict) -> str:
        """Recursively extract plain text body from email payload."""
        body = ""

        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    data = part.get("body", {}).get("data", "")
                    if data:
                        body += base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                elif part["mimeType"].startswith("multipart/"):
                    body += self._extract_body(part)
        else:
            data = payload.get("body", {}).get("data", "")
            if data:
                body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

        return body.strip()

    def get_thread_context(self, thread_id: str, limit: int = 3) -> str:
        """
        Get the last few messages in a thread as context for the AI.
        Returns a formatted string of the conversation history.
        """
        try:
            thread = self.service.users().threads().get(
                userId="me", id=thread_id, format="full"
            ).execute()

            messages = thread.get("messages", [])[-limit:]
            context_parts = []

            for msg in messages:
                headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
                sender = headers.get("From", "unknown")
                date = headers.get("Date", "")
                body = self._extract_body(msg["payload"])
                context_parts.append(f"From: {sender}\nDate: {date}\n{body[:500]}")

            return "\n\n---\n\n".join(context_parts)

        except HttpError as e:
            logger.warning(f"Could not fetch thread context for {thread_id}: {e}")
            return ""

    def send_reply(self, original_message_id: str, thread_id: str, to: str, subject: str, body: str):
        """Send a reply to an email thread."""
        import email as email_lib
        from email.mime.text import MIMEText

        msg = MIMEText(body)
        msg["To"] = to
        msg["Subject"] = f"Re: {subject}" if not subject.startswith("Re:") else subject
        msg["In-Reply-To"] = original_message_id
        msg["References"] = original_message_id

        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

        try:
            self.service.users().messages().send(
                userId="me",
                body={"raw": raw, "threadId": thread_id},
            ).execute()
            logger.info(f"Reply sent to {to} — subject: {subject}")
        except HttpError as e:
            logger.error(f"Failed to send reply: {e}")
            raise

    def mark_as_read(self, message_id: str):
        """Remove UNREAD label from a message."""
        try:
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]},
            ).execute()
        except HttpError as e:
            logger.warning(f"Could not mark message {message_id} as read: {e}")

    def apply_label(self, message_id: str, label_name: str):
        """
        Apply a Gmail label (creates label if it doesn't exist).
        Used to tag emails as 'AI-Replied' or 'Needs-Human'.
        """
        try:
            label_id = self._get_or_create_label(label_name)
            self.service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"addLabelIds": [label_id]},
            ).execute()
        except HttpError as e:
            logger.warning(f"Could not apply label '{label_name}': {e}")

    def _get_or_create_label(self, label_name: str) -> str:
        """Return label ID, creating the label if it doesn't already exist."""
        labels_result = self.service.users().labels().list(userId="me").execute()
        labels = labels_result.get("labels", [])

        for label in labels:
            if label["name"] == label_name:
                return label["id"]

        # Create new label
        new_label = self.service.users().labels().create(
            userId="me",
            body={
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        ).execute()
        logger.info(f"Created Gmail label: {label_name}")
        return new_label["id"]
