"""
SQLite database for Apprenticeship Applier.
Tracks all found and applied-to jobs to prevent re-applying.
"""

import sqlite3
from datetime import datetime
from typing import Optional, List
from config import Config


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't already exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                url                 TEXT    UNIQUE NOT NULL,
                title               TEXT,
                company             TEXT,
                location            TEXT,
                wage                TEXT,
                closing_date        TEXT,
                apprenticeship_level TEXT,
                description_snippet TEXT,
                status              TEXT    NOT NULL DEFAULT 'found',
                -- status: found | applied | skipped | failed | captcha_blocked
                applied_at          TEXT,
                cover_letter_path   TEXT,
                screenshot_path     TEXT,
                found_at            TEXT    NOT NULL,
                notes               TEXT
            )
        """)
        conn.commit()


def is_seen(url: str) -> bool:
    """Return True if this job URL has been processed before."""
    with get_connection() as conn:
        row = conn.execute("SELECT 1 FROM jobs WHERE url = ?", (url,)).fetchone()
        return row is not None


def add_job(
    url: str,
    title: str,
    company: str,
    location: str,
    wage: str = "",
    closing_date: str = "",
    apprenticeship_level: str = "",
    description_snippet: str = "",
):
    """Insert a newly found job listing."""
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO jobs
                (url, title, company, location, wage, closing_date,
                 apprenticeship_level, description_snippet, status, found_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'found', ?)
            """,
            (url, title, company, location, wage, closing_date,
             apprenticeship_level, description_snippet[:500], now),
        )
        conn.commit()


def update_status(
    url: str,
    status: str,
    cover_letter_path: Optional[str] = None,
    screenshot_path: Optional[str] = None,
    notes: Optional[str] = None,
):
    """Update the status of a job after processing."""
    now = datetime.utcnow().isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE jobs SET
                status = ?,
                applied_at = CASE WHEN ? = 'applied' THEN ? ELSE applied_at END,
                cover_letter_path = COALESCE(?, cover_letter_path),
                screenshot_path   = COALESCE(?, screenshot_path),
                notes             = COALESCE(?, notes)
            WHERE url = ?
            """,
            (status, status, now, cover_letter_path, screenshot_path, notes, url),
        )
        conn.commit()


def get_pending_jobs(limit: int = None) -> List[sqlite3.Row]:
    """Return jobs with status 'found' (not yet applied)."""
    query = "SELECT * FROM jobs WHERE status = 'found' ORDER BY found_at DESC"
    if limit:
        query += f" LIMIT {limit}"
    with get_connection() as conn:
        return conn.execute(query).fetchall()


def get_stats() -> dict:
    """Return a summary of job statuses."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT status, COUNT(*) as count FROM jobs GROUP BY status
        """).fetchall()
        return {row["status"]: row["count"] for row in rows}
