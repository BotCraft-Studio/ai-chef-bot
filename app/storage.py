import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data.sqlite"

def _cx():
    return sqlite3.connect(DB_PATH)

def init_db():
    with _cx() as cx:
        cx.execute("""
        CREATE TABLE IF NOT EXISTS users (
          user_id INTEGER PRIMARY KEY,
          daily_time TEXT DEFAULT '09:00',
          daily_enabled INTEGER DEFAULT 0
        );
        """)
        cx.execute("""
        CREATE TABLE IF NOT EXISTS ingredients (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          name TEXT NOT NULL,
          added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cx.commit()

def upsert_user(user_id: int, daily_time: str | None = None, enabled: int | None = None):
    with _cx() as cx:
        cx.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
        if daily_time is not None:
            cx.execute("UPDATE users SET daily_time=? WHERE user_id=?", (daily_time, user_id))
        if enabled is not None:
            cx.execute("UPDATE users SET daily_enabled=? WHERE user_id=?", (enabled, user_id))
        cx.commit()

def list_ingredients(user_id: int):
    with _cx() as cx:
        cur = cx.execute("SELECT id,name,added_at FROM ingredients WHERE user_id=? ORDER BY id DESC", (user_id,))
        return cur.fetchall()

def add_ingredients(user_id: int, items: list[str]):
    items = [i.strip() for i in items if i.strip()]
    if not items:
        return
    with _cx() as cx:
        cx.executemany("INSERT INTO ingredients(user_id,name) VALUES(?,?)", [(user_id, i) for i in items])
        cx.commit()

def clear_ingredients(user_id: int):
    with _cx() as cx:
        cx.execute("DELETE FROM ingredients WHERE user_id=?", (user_id,))
        cx.commit()
