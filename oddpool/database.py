"""SQLite tracker for oddpool arb trades."""

import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "oddpool.db"


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS arbs (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date    TEXT NOT NULL,
            poly_id       TEXT NOT NULL,
            kalshi_id     TEXT NOT NULL,
            event_title   TEXT,
            buy_yes_on    TEXT,        -- 'polymarket' or 'kalshi'
            yes_price     REAL,
            no_price      REAL,
            bundle_cost   REAL,
            net_edge      REAL,
            shared_words  TEXT,
            pnl_usd       REAL,
            status        TEXT DEFAULT 'open',
            opened_at     TEXT NOT NULL,
            closed_at     TEXT
        );
        CREATE TABLE IF NOT EXISTS daily_summary (
            trade_date  TEXT PRIMARY KEY,
            arbs        INTEGER DEFAULT 0,
            pnl_usd     REAL DEFAULT 0,
            pnl_gbp     REAL DEFAULT 0,
            stopped     INTEGER DEFAULT 0
        );
        """)


def _today(): return date.today().isoformat()
def _now():   return datetime.utcnow().isoformat()

def _ensure(c, td):
    c.execute("INSERT OR IGNORE INTO daily_summary (trade_date) VALUES (?)", (td,))


def is_stopped() -> bool:
    with _conn() as c:
        r = c.execute("SELECT stopped FROM daily_summary WHERE trade_date=?", (_today(),)).fetchone()
        return bool(r and r["stopped"])


def get_daily() -> dict:
    with _conn() as c:
        r = c.execute("SELECT * FROM daily_summary WHERE trade_date=?", (_today(),)).fetchone()
        return dict(r) if r else {"arbs": 0, "pnl_usd": 0.0, "pnl_gbp": 0.0, "stopped": 0}


def log_arb_open(poly_id, kalshi_id, event_title, buy_yes_on,
                  yes_price, no_price, bundle_cost, net_edge, shared_words) -> Optional[int]:
    td = _today()
    with _conn() as c:
        _ensure(c, td)
        cur = c.execute(
            """INSERT INTO arbs
               (trade_date,poly_id,kalshi_id,event_title,buy_yes_on,
                yes_price,no_price,bundle_cost,net_edge,shared_words,opened_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (td, poly_id, kalshi_id, event_title, buy_yes_on,
             yes_price, no_price, bundle_cost, net_edge, shared_words, _now())
        )
        c.execute("UPDATE daily_summary SET arbs=arbs+1 WHERE trade_date=?", (td,))
        return cur.lastrowid


def log_arb_close(arb_id: int, pnl_usd: float, gbp_rate: float = 1.27):
    td = _today()
    with _conn() as c:
        _ensure(c, td)
        c.execute(
            "UPDATE arbs SET pnl_usd=?,status='closed',closed_at=? WHERE id=?",
            (pnl_usd, _now(), arb_id)
        )
        c.execute(
            "UPDATE daily_summary SET pnl_usd=pnl_usd+?,pnl_gbp=pnl_gbp+? WHERE trade_date=?",
            (pnl_usd, pnl_usd / gbp_rate, td)
        )


def mark_stopped():
    td = _today()
    with _conn() as c:
        _ensure(c, td)
        c.execute("UPDATE daily_summary SET stopped=1 WHERE trade_date=?", (td,))


def get_open_arbs() -> list:
    with _conn() as c:
        return [dict(r) for r in c.execute("SELECT * FROM arbs WHERE status='open'").fetchall()]


def print_report():
    with _conn() as c:
        rows = c.execute("SELECT * FROM daily_summary ORDER BY trade_date DESC LIMIT 30").fetchall()
        print(f"\n{'Date':<12} {'Arbs':>5} {'P&L USD':>9} {'P&L GBP':>8} {'Stopped':>8}")
        print("-" * 46)
        for r in rows:
            print(f"{r['trade_date']:<12} {r['arbs']:>5} ${r['pnl_usd']:>8.2f} "
                  f"£{r['pnl_gbp']:>7.2f} {'YES' if r['stopped'] else '':>8}")

        print("\nRecent arbs:")
        arbs = c.execute(
            "SELECT * FROM arbs ORDER BY opened_at DESC LIMIT 20"
        ).fetchall()
        print(f"{'Date':<12} {'Event':<45} {'Edge':>6} {'P&L':>8} {'Status':>8}")
        print("-" * 82)
        for a in arbs:
            title = (a['event_title'] or '')[:44]
            pnl   = f"${a['pnl_usd']:+.2f}" if a['pnl_usd'] is not None else "open"
            print(f"{a['trade_date']:<12} {title:<45} {a['net_edge']*100:>5.1f}¢ {pnl:>8} {a['status']:>8}")
