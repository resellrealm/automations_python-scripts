"""
SQLite tracker — trades, daily P&L, positions.
"""
import sqlite3
from datetime import date, datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "flipper.db"


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS trades (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date   TEXT NOT NULL,
            strategy     TEXT NOT NULL,
            market_id    TEXT NOT NULL,
            token_id     TEXT NOT NULL,
            side         TEXT NOT NULL,
            size         REAL NOT NULL,
            entry_price  REAL NOT NULL,
            exit_price   REAL,
            pnl_usdc     REAL,
            status       TEXT DEFAULT 'open',
            reason       TEXT,
            opened_at    TEXT NOT NULL,
            closed_at    TEXT
        );
        CREATE TABLE IF NOT EXISTS daily_summary (
            trade_date        TEXT PRIMARY KEY,
            trades            INTEGER DEFAULT 0,
            pnl_usdc          REAL DEFAULT 0,
            pnl_gbp           REAL DEFAULT 0,
            end_balance_gbp   REAL DEFAULT 0,
            stopped           INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS balance_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            recorded_at TEXT NOT NULL,
            balance_gbp REAL NOT NULL,
            note        TEXT
        );
        """)


def get_today() -> str:
    return date.today().isoformat()


def get_daily(trade_date: str = None) -> dict:
    td = trade_date or get_today()
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM daily_summary WHERE trade_date = ?", (td,)
        ).fetchone()
        if row:
            return dict(row)
        return {"trade_date": td, "trades": 0, "pnl_usdc": 0.0, "pnl_gbp": 0.0, "stopped": 0}


def is_stopped_today() -> bool:
    return bool(get_daily().get("stopped"))


def _ensure_daily(c, td):
    c.execute(
        "INSERT OR IGNORE INTO daily_summary (trade_date) VALUES (?)", (td,)
    )


def log_trade_open(strategy, market_id, token_id, side, size, entry_price, reason) -> int:
    td = get_today()
    now = datetime.utcnow().isoformat()
    with _conn() as c:
        _ensure_daily(c, td)
        cur = c.execute(
            """INSERT INTO trades
               (trade_date, strategy, market_id, token_id, side, size, entry_price, reason, opened_at, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')""",
            (td, strategy, market_id, token_id, side, size, entry_price, reason, now)
        )
        c.execute(
            "UPDATE daily_summary SET trades = trades + 1 WHERE trade_date = ?", (td,)
        )
        return cur.lastrowid


def log_trade_close(trade_id: int, exit_price: float, pnl_usdc: float, gbp_rate: float = 1.27):
    td = get_today()
    now = datetime.utcnow().isoformat()
    pnl_gbp = pnl_usdc / gbp_rate
    with _conn() as c:
        _ensure_daily(c, td)
        c.execute(
            """UPDATE trades SET exit_price=?, pnl_usdc=?, status='closed', closed_at=?
               WHERE id=?""",
            (exit_price, pnl_usdc, now, trade_id)
        )
        c.execute(
            """UPDATE daily_summary SET pnl_usdc = pnl_usdc + ?, pnl_gbp = pnl_gbp + ?
               WHERE trade_date = ?""",
            (pnl_usdc, pnl_gbp, td)
        )


def mark_daily_stopped():
    td = get_today()
    with _conn() as c:
        _ensure_daily(c, td)
        c.execute(
            "UPDATE daily_summary SET stopped = 1 WHERE trade_date = ?", (td,)
        )


def count_open_trades() -> int:
    with _conn() as c:
        row = c.execute(
            "SELECT COUNT(*) as n FROM trades WHERE trade_date = ? AND status = 'open'",
            (get_today(),)
        ).fetchone()
        return row["n"] if row else 0


def get_open_trades() -> list:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM trades WHERE status = 'open'"
        ).fetchall()
        return [dict(r) for r in rows]


def snapshot_balance(balance_gbp: float, note: str = ""):
    """Record a balance snapshot for growth tracking."""
    now = datetime.utcnow().isoformat()
    with _conn() as c:
        c.execute(
            "INSERT INTO balance_history (recorded_at, balance_gbp, note) VALUES (?, ?, ?)",
            (now, balance_gbp, note)
        )


def print_report():
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM daily_summary ORDER BY trade_date DESC LIMIT 30"
        ).fetchall()
        print(f"\n{'Date':<12} {'Trades':>6} {'P&L USDC':>10} {'P&L GBP':>9} {'Balance':>9} {'Stopped':>8}")
        print("-" * 60)
        for r in rows:
            stopped = "YES" if r["stopped"] else ""
            bal = f"£{r['end_balance_gbp']:.2f}" if r["end_balance_gbp"] else "—"
            print(
                f"{r['trade_date']:<12} {r['trades']:>6} "
                f"${r['pnl_usdc']:>9.2f} £{r['pnl_gbp']:>8.2f} {bal:>9} {stopped:>8}"
            )
