"""SQLite trade journal for the trading bot."""
import sqlite3
from datetime import datetime
from typing import Optional, List
from config import Config


def get_conn():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                pair          TEXT    NOT NULL,
                side          TEXT    NOT NULL,
                strategy      TEXT,
                entry_price   REAL,
                exit_price    REAL,
                size          REAL,
                stop_price    REAL,
                take_profit   REAL,
                pnl           REAL,
                pnl_pct       REAL,
                exit_reason   TEXT,
                status        TEXT    NOT NULL DEFAULT 'open',
                opened_at     TEXT    NOT NULL,
                closed_at     TEXT,
                dry_run       INTEGER NOT NULL DEFAULT 1,
                notes         TEXT
            )
        """)
        conn.commit()


def open_trade(pair, side, strategy, entry_price, size, stop_price, take_profit, dry_run=True) -> int:
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO trades (pair, side, strategy, entry_price, size, stop_price, take_profit, opened_at, dry_run)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pair, side, strategy, entry_price, size, stop_price, take_profit,
               datetime.utcnow().isoformat(), int(dry_run)))
        conn.commit()
        return cur.lastrowid


def close_trade(trade_id: int, exit_price: float, exit_reason: str):
    with get_conn() as conn:
        trade = conn.execute("SELECT * FROM trades WHERE id = ?", (trade_id,)).fetchone()
        if not trade:
            return
        pnl = (exit_price - trade["entry_price"]) * trade["size"]
        pnl_pct = ((exit_price - trade["entry_price"]) / trade["entry_price"]) * 100
        conn.execute("""
            UPDATE trades SET exit_price=?, exit_reason=?, pnl=?, pnl_pct=?,
                              status='closed', closed_at=?
            WHERE id=?
        """, (exit_price, exit_reason, round(pnl, 4), round(pnl_pct, 2),
               datetime.utcnow().isoformat(), trade_id))
        conn.commit()


def get_open_trades() -> List[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM trades WHERE status = 'open'").fetchall()


def get_summary() -> dict:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                   SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losses,
                   ROUND(SUM(pnl), 2) as total_pnl,
                   ROUND(AVG(pnl_pct), 2) as avg_pnl_pct
            FROM trades WHERE status = 'closed'
        """).fetchone()
        open_count = conn.execute("SELECT COUNT(*) FROM trades WHERE status = 'open'").fetchone()[0]
        return dict(rows) | {"open": open_count}
