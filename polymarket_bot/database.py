"""Position tracker for Polymarket bot."""
import sqlite3
from datetime import datetime
from typing import List
from config import Config


def get_conn():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                market_id     TEXT,
                question      TEXT,
                strategy      TEXT,
                action        TEXT,
                token_id      TEXT,
                entry_price   REAL,
                exit_price    REAL,
                size          REAL,
                pnl           REAL,
                pnl_pct       REAL,
                status        TEXT DEFAULT 'open',
                reason        TEXT,
                opened_at     TEXT,
                closed_at     TEXT,
                dry_run       INTEGER DEFAULT 1
            )
        """)
        conn.commit()


def open_position(market_id, question, strategy, action, token_id, entry_price, size, reason, dry_run=True) -> int:
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO positions (market_id, question, strategy, action, token_id, entry_price, size, reason, opened_at, dry_run)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (market_id, question, strategy, action, token_id, entry_price, size, reason,
               datetime.utcnow().isoformat(), int(dry_run)))
        conn.commit()
        return cur.lastrowid


def close_position(pos_id: int, exit_price: float):
    with get_conn() as conn:
        pos = conn.execute("SELECT * FROM positions WHERE id=?", (pos_id,)).fetchone()
        if not pos:
            return
        pnl = (exit_price - pos["entry_price"]) * pos["size"]
        pnl_pct = ((exit_price - pos["entry_price"]) / max(pos["entry_price"], 0.01)) * 100
        conn.execute("""
            UPDATE positions SET exit_price=?, pnl=?, pnl_pct=?, status='closed', closed_at=? WHERE id=?
        """, (exit_price, round(pnl, 4), round(pnl_pct, 2), datetime.utcnow().isoformat(), pos_id))
        conn.commit()


def get_open_positions() -> List[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM positions WHERE status='open'").fetchall()


def get_summary() -> dict:
    with get_conn() as conn:
        r = conn.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN pnl>0 THEN 1 ELSE 0 END) as wins,
                   ROUND(SUM(pnl),2) as total_pnl,
                   ROUND(AVG(pnl_pct),2) as avg_pnl_pct
            FROM positions WHERE status='closed'
        """).fetchone()
        open_c = conn.execute("SELECT COUNT(*) FROM positions WHERE status='open'").fetchone()[0]
        return dict(r) | {"open": open_c}
