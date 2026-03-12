"""SQLite tracker — trades and daily P&L."""

import sqlite3
from datetime import date, datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "kalshi_flipper.db"


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS trades (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date  TEXT NOT NULL,
            strategy    TEXT NOT NULL,
            ticker      TEXT NOT NULL,
            side        TEXT NOT NULL,
            contracts   INTEGER NOT NULL,
            entry_cents INTEGER NOT NULL,
            exit_cents  INTEGER,
            pnl_usd     REAL,
            status      TEXT DEFAULT 'open',
            reason      TEXT,
            opened_at   TEXT NOT NULL,
            closed_at   TEXT
        );
        CREATE TABLE IF NOT EXISTS daily_summary (
            trade_date  TEXT PRIMARY KEY,
            trades      INTEGER DEFAULT 0,
            pnl_usd     REAL DEFAULT 0,
            pnl_gbp     REAL DEFAULT 0,
            stopped     INTEGER DEFAULT 0
        );
        """)


def _today(): return date.today().isoformat()
def _now():   return datetime.utcnow().isoformat()


def _ensure_daily(c, td):
    c.execute("INSERT OR IGNORE INTO daily_summary (trade_date) VALUES (?)", (td,))


def is_stopped() -> bool:
    with _conn() as c:
        r = c.execute("SELECT stopped FROM daily_summary WHERE trade_date=?", (_today(),)).fetchone()
        return bool(r and r["stopped"])


def get_daily() -> dict:
    with _conn() as c:
        r = c.execute("SELECT * FROM daily_summary WHERE trade_date=?", (_today(),)).fetchone()
        return dict(r) if r else {"trades": 0, "pnl_usd": 0.0, "pnl_gbp": 0.0, "stopped": 0}


def log_open(strategy, ticker, side, contracts, entry_cents, reason) -> int:
    td = _today()
    with _conn() as c:
        _ensure_daily(c, td)
        cur = c.execute(
            "INSERT INTO trades (trade_date,strategy,ticker,side,contracts,entry_cents,reason,opened_at,status) "
            "VALUES (?,?,?,?,?,?,?,?,'open')",
            (td, strategy, ticker, side, contracts, entry_cents, reason, _now())
        )
        c.execute("UPDATE daily_summary SET trades=trades+1 WHERE trade_date=?", (td,))
        return cur.lastrowid


def log_close(trade_id: int, exit_cents: int, pnl_usd: float, gbp_rate=1.27):
    td = _today()
    pnl_gbp = pnl_usd / gbp_rate
    with _conn() as c:
        _ensure_daily(c, td)
        c.execute(
            "UPDATE trades SET exit_cents=?,pnl_usd=?,status='closed',closed_at=? WHERE id=?",
            (exit_cents, pnl_usd, _now(), trade_id)
        )
        c.execute(
            "UPDATE daily_summary SET pnl_usd=pnl_usd+?,pnl_gbp=pnl_gbp+? WHERE trade_date=?",
            (pnl_usd, pnl_gbp, td)
        )


def mark_stopped():
    td = _today()
    with _conn() as c:
        _ensure_daily(c, td)
        c.execute("UPDATE daily_summary SET stopped=1 WHERE trade_date=?", (td,))


def get_open_trades() -> list:
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM trades WHERE status='open'").fetchall()]


def print_report():
    with _conn() as c:
        rows = c.execute("SELECT * FROM daily_summary ORDER BY trade_date DESC LIMIT 30").fetchall()
        print(f"\n{'Date':<12} {'Trades':>6} {'P&L USD':>9} {'P&L GBP':>8} {'Stopped':>8}")
        print("-" * 48)
        for r in rows:
            print(f"{r['trade_date']:<12} {r['trades']:>6} ${r['pnl_usd']:>8.2f} "
                  f"£{r['pnl_gbp']:>7.2f} {'YES' if r['stopped'] else '':>8}")
