import sqlite3
import os
from typing import Optional, Any

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "touzi.db")


def _get_conn() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS funds (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            code  TEXT UNIQUE NOT NULL,
            name  TEXT NOT NULL,
            type  TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            fund_id  INTEGER NOT NULL,
            type     TEXT NOT NULL CHECK(type IN ('buy','sell')),
            date     TEXT NOT NULL,
            amount   REAL NOT NULL,
            shares   REAL,
            nav      REAL,
            fee      REAL DEFAULT 0,
            note     TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (fund_id) REFERENCES funds(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_tx_fund   ON transactions(fund_id);
        CREATE INDEX IF NOT EXISTS idx_tx_date   ON transactions(date);
    """)
    conn.commit()
    conn.close()


# ── Fund CRUD ──────────────────────────────────────────────

def add_fund(code: str, name: str, type_: str = "") -> int:
    conn = _get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO funds (code, name, type) VALUES (?, ?, ?)",
            (code, name, type_),
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError(f"基金代码「{code}」已存在")
    finally:
        conn.close()


def get_all_funds() -> list[dict[str, Any]]:
    conn = _get_conn()
    rows = conn.execute("SELECT * FROM funds ORDER BY code").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_fund(fund_id: int) -> Optional[dict[str, Any]]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM funds WHERE id = ?", (fund_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_fund(fund_id: int, code: str, name: str, type_: str = ""):
    conn = _get_conn()
    conn.execute(
        "UPDATE funds SET code = ?, name = ?, type = ? WHERE id = ?",
        (code, name, type_, fund_id),
    )
    conn.commit()
    conn.close()


def delete_fund(fund_id: int):
    conn = _get_conn()
    conn.execute("DELETE FROM transactions WHERE fund_id = ?", (fund_id,))
    conn.execute("DELETE FROM funds WHERE id = ?", (fund_id,))
    conn.commit()
    conn.close()


# ── Transaction CRUD ───────────────────────────────────────

def add_transaction(
    fund_id: int,
    type_: str,
    date_: str,
    amount: float,
    shares: Optional[float] = None,
    nav: Optional[float] = None,
    fee: float = 0.0,
    note: str = "",
) -> int:
    conn = _get_conn()
    cur = conn.execute(
        "INSERT INTO transactions (fund_id, type, date, amount, shares, nav, fee, note) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (fund_id, type_, date_, amount, shares, nav, fee, note),
    )
    conn.commit()
    conn.close()
    return cur.lastrowid


def get_transactions(fund_id: Optional[int] = None) -> list[dict[str, Any]]:
    conn = _get_conn()
    if fund_id is not None:
        rows = conn.execute(
            "SELECT * FROM transactions WHERE fund_id = ? ORDER BY date, id",
            (fund_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT t.*, f.code, f.name "
            "FROM transactions t JOIN funds f ON t.fund_id = f.id "
            "ORDER BY t.date, t.id"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_transaction(
    tx_id: int,
    fund_id: int,
    type_: str,
    date_: str,
    amount: float,
    shares: Optional[float] = None,
    nav: Optional[float] = None,
    fee: float = 0.0,
    note: str = "",
):
    conn = _get_conn()
    conn.execute(
        "UPDATE transactions SET fund_id=?, type=?, date=?, amount=?, shares=?, nav=?, fee=?, note=? "
        "WHERE id=?",
        (fund_id, type_, date_, amount, shares, nav, fee, note, tx_id),
    )
    conn.commit()
    conn.close()


def delete_transaction(tx_id: int):
    conn = _get_conn()
    conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()
