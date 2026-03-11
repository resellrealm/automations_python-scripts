"""
SQLite database for Email Auto-Replier.
Tracks all processed emails to prevent duplicate replies.
"""

import sqlite3
from datetime import datetime
from typing import Optional
from config import Config


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't already exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_emails (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id      TEXT    UNIQUE NOT NULL,
                thread_id       TEXT,
                sender          TEXT,
                subject         TEXT,
                received_at     TEXT,
                action          TEXT    NOT NULL,   -- 'replied' | 'escalated' | 'skipped'
                ai_confidence   REAL,
                escalation_reason TEXT,
                reply_preview   TEXT,               -- first 300 chars of reply sent
                processed_at    TEXT    NOT NULL,
                error           TEXT                -- non-null if processing failed
            )
        """)
        conn.commit()


def is_processed(message_id: str) -> bool:
    """Return True if this email has already been handled."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM processed_emails WHERE message_id = ?", (message_id,)
        ).fetchone()
        return row is not None


def record_email(
    message_id: str,
    thread_id: str,
    sender: str,
    subject: str,
    received_at: str,
    action: str,
    ai_confidence: Optional[float] = None,
    escalation_reason: Optional[str] = None,
    reply_preview: Optional[str] = None,
    error: Optional[str] = None,
):
    """Insert a record for a processed email."""
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO processed_emails
                (message_id, thread_id, sender, subject, received_at,
                 action, ai_confidence, escalation_reason, reply_preview,
                 processed_at, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id, thread_id, sender, subject, received_at,
                action, ai_confidence, escalation_reason,
                reply_preview[:300] if reply_preview else None,
                now, error,
            ),
        )
        conn.commit()


def get_stats() -> dict:
    """Return a summary of processing stats."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT action, COUNT(*) as count
            FROM processed_emails
            GROUP BY action
        """).fetchall()
        return {row["action"]: row["count"] for row in rows}
