"""
SQLite database — Email Auto-Replier
Tables:
  processed_emails  — all handled emails (replied, escalated, error)
  pending_replies   — queued replies waiting for 1-hour send delay
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List
from config import Config


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_emails (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id        TEXT    UNIQUE NOT NULL,
                thread_id         TEXT,
                sender            TEXT,
                subject           TEXT,
                received_at       TEXT,
                action            TEXT    NOT NULL,
                ai_confidence     REAL,
                escalation_reason TEXT,
                reply_preview     TEXT,
                processed_at      TEXT    NOT NULL,
                error             TEXT
            )
        """)
        # Pending replies queue — holds replies until 1 hour after email received
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pending_replies (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id    TEXT    UNIQUE NOT NULL,
                uid           TEXT    NOT NULL,
                sender        TEXT    NOT NULL,
                subject       TEXT    NOT NULL,
                reply_text    TEXT    NOT NULL,
                received_at   TEXT    NOT NULL,
                send_at       TEXT    NOT NULL,   -- UTC ISO timestamp: received + 1 hour
                sent          INTEGER NOT NULL DEFAULT 0,
                sent_at       TEXT
            )
        """)
        conn.commit()


def is_processed(message_id: str) -> bool:
    with get_connection() as conn:
        return conn.execute(
            "SELECT 1 FROM processed_emails WHERE message_id = ?", (message_id,)
        ).fetchone() is not None


def is_reply_pending(message_id: str) -> bool:
    with get_connection() as conn:
        return conn.execute(
            "SELECT 1 FROM pending_replies WHERE message_id = ? AND sent = 0", (message_id,)
        ).fetchone() is not None


def queue_reply(
    uid: str,
    message_id: str,
    sender: str,
    subject: str,
    reply_text: str,
    received_at: str,
    delay_hours: float = 1.0,
):
    """Queue a reply to be sent after delay_hours (default 1 hour)."""
    send_at = (datetime.utcnow() + timedelta(hours=delay_hours)).isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO pending_replies
                (message_id, uid, sender, subject, reply_text, received_at, send_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (message_id, uid, sender, subject, reply_text, received_at, send_at),
        )
        conn.commit()


def get_due_replies() -> List[sqlite3.Row]:
    """Return all unsent replies whose send_at time has passed."""
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM pending_replies WHERE sent = 0 AND send_at <= ?", (now,)
        ).fetchall()


def mark_reply_sent(message_id: str):
    with get_connection() as conn:
        conn.execute(
            "UPDATE pending_replies SET sent = 1, sent_at = ? WHERE message_id = ?",
            (datetime.utcnow().isoformat(), message_id),
        )
        conn.commit()


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
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO processed_emails
                (message_id, thread_id, sender, subject, received_at,
                 action, ai_confidence, escalation_reason, reply_preview, processed_at, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (message_id, thread_id, sender, subject, received_at, action,
             ai_confidence, escalation_reason,
             reply_preview[:300] if reply_preview else None, now, error),
        )
        conn.commit()


def get_stats() -> dict:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT action, COUNT(*) as count FROM processed_emails GROUP BY action"
        ).fetchall()
        stats = {row["action"]: row["count"] for row in rows}

        pending = conn.execute(
            "SELECT COUNT(*) as count FROM pending_replies WHERE sent = 0"
        ).fetchone()
        stats["pending_queue"] = pending["count"]
        return stats
