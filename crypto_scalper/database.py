"""
SQLite trade log — Crypto Scalper
"""
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "scalper.db"


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
            symbol       TEXT NOT NULL,
            direction    TEXT NOT NULL,
            size_gbp     REAL NOT NULL,
            size_usdt    REAL NOT NULL,
            entry_price  REAL NOT NULL,
            sl_price     REAL NOT NULL,
            tp_price     REAL NOT NULL,
            exit_price   REAL,
            exit_reason  TEXT,
            pnl_gbp      REAL,
            confidence   REAL NOT NULL,
            atr          REAL NOT NULL,
            status       TEXT DEFAULT 'open',
            reason       TEXT,
            opened_at    TEXT NOT NULL,
            closed_at    TEXT,
            order_id     TEXT
        );
        CREATE TABLE IF NOT EXISTS daily_summary (
            trade_date TEXT PRIMARY KEY,
            trades     INTEGER DEFAULT 0,
            wins       INTEGER DEFAULT 0,
            pnl_gbp    REAL DEFAULT 0,
            stopped    INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS balance_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            recorded_at TEXT NOT NULL,
            balance_gbp REAL NOT NULL,
            note        TEXT
        );
        """)


def _today() -> str:
    return date.today().isoformat()


def _ensure_daily(c, td):
    c.execute("INSERT OR IGNORE INTO daily_summary (trade_date) VALUES (?)", (td,))


def log_trade_open(
    symbol: str, direction: str, size_gbp: float, size_usdt: float,
    entry_price: float, sl_price: float, tp_price: float,
    confidence: float, atr: float, reason: str, order_id: str = "",
) -> int:
    td  = _today()
    now = datetime.utcnow().isoformat()
    with _conn() as c:
        _ensure_daily(c, td)
        cur = c.execute(
            """INSERT INTO trades
               (trade_date, symbol, direction, size_gbp, size_usdt, entry_price,
                sl_price, tp_price, confidence, atr, reason, opened_at, status, order_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)""",
            (td, symbol, direction, size_gbp, size_usdt, entry_price,
             sl_price, tp_price, confidence, atr, reason, now, order_id),
        )
        c.execute("UPDATE daily_summary SET trades = trades + 1 WHERE trade_date = ?", (td,))
        return cur.lastrowid


def log_trade_close(trade_id: int, exit_price: float, exit_reason: str, pnl_gbp: float):
    td  = _today()
    now = datetime.utcnow().isoformat()
    won = 1 if pnl_gbp > 0 else 0
    with _conn() as c:
        _ensure_daily(c, td)
        c.execute(
            """UPDATE trades SET exit_price=?, exit_reason=?, pnl_gbp=?,
               status='closed', closed_at=? WHERE id=?""",
            (exit_price, exit_reason, pnl_gbp, now, trade_id),
        )
        c.execute(
            "UPDATE daily_summary SET pnl_gbp = pnl_gbp + ?, wins = wins + ? WHERE trade_date = ?",
            (pnl_gbp, won, td),
        )


def count_open_trades() -> int:
    with _conn() as c:
        row = c.execute("SELECT COUNT(*) as n FROM trades WHERE status = 'open'").fetchone()
        return row["n"] if row else 0


def count_today_trades() -> int:
    with _conn() as c:
        row = c.execute(
            "SELECT COUNT(*) as n FROM trades WHERE trade_date = ?", (_today(),)
        ).fetchone()
        return row["n"] if row else 0


def get_open_trades() -> list:
    with _conn() as c:
        rows = c.execute("SELECT * FROM trades WHERE status = 'open'").fetchall()
        return [dict(r) for r in rows]


def get_stale_trades(max_hold_minutes: int) -> list:
    cutoff = (datetime.utcnow() - timedelta(minutes=max_hold_minutes)).isoformat()
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM trades WHERE status = 'open' AND opened_at < ?", (cutoff,)
        ).fetchall()
        return [dict(r) for r in rows]


def snapshot_balance(balance_gbp: float, note: str = ""):
    now = datetime.utcnow().isoformat()
    with _conn() as c:
        c.execute(
            "INSERT INTO balance_history (recorded_at, balance_gbp, note) VALUES (?, ?, ?)",
            (now, balance_gbp, note),
        )


def print_report():
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM daily_summary ORDER BY trade_date DESC LIMIT 30"
        ).fetchall()
    print(f"\n{'Date':<12} {'Trades':>6} {'Wins':>5} {'P&L GBP':>10} {'Stopped':>8}")
    print("-" * 48)
    for r in rows:
        stopped = "YES" if r["stopped"] else ""
        print(
            f"{r['trade_date']:<12} {r['trades']:>6} {r['wins']:>5} "
            f"£{r['pnl_gbp']:>9.2f} {stopped:>8}"
        )
