import os
import sqlite3
from contextlib import contextmanager

DB_PATH = os.path.join("data", "fate_v1.db")


def ensure_data_dir() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_connection() -> sqlite3.Connection:
    ensure_data_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_connection():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    ensure_data_dir()
    with db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                "group" TEXT NOT NULL,
                min_desc TEXT,
                normal_desc TEXT,
                min_xp INTEGER DEFAULT 1,
                normal_xp INTEGER DEFAULT 2,
                active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS habit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                habit_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                minutes INTEGER,
                note TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                UNIQUE(date, habit_id),
                FOREIGN KEY (habit_id) REFERENCES habits(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS habit_schedules (
                habit_id INTEGER PRIMARY KEY,
                schedule_type TEXT NOT NULL DEFAULT 'always',
                weekly_days TEXT,
                interval_days INTEGER,
                anchor_date TEXT,
                cooldown_days INTEGER,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (habit_id) REFERENCES habits(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                ultimate_goal TEXT,
                active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                line_id INTEGER NOT NULL,
                chapter TEXT,
                order_idx INTEGER NOT NULL,
                title TEXT NOT NULL,
                dod TEXT,
                difficulty INTEGER NOT NULL,
                is_boss INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (line_id) REFERENCES lines(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quest_completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                quest_id INTEGER NOT NULL,
                minutes INTEGER,
                evidence_type TEXT,
                evidence_text TEXT NOT NULL,
                evidence_ref TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (quest_id) REFERENCES quests(id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evidence_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews_weekly (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start TEXT NOT NULL UNIQUE,
                effective TEXT,
                friction TEXT,
                next_change TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ui_labels (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO habit_schedules (habit_id, schedule_type)
            SELECT h.id, 'always'
            FROM habits h
            WHERE h.id NOT IN (SELECT habit_id FROM habit_schedules)
            """
        )
        count = conn.execute("SELECT COUNT(*) AS c FROM evidence_types").fetchone()["c"]
        if count == 0:
            defaults = [
                ("commit", 1, 0),
                ("file", 1, 1),
                ("issue", 1, 2),
                ("note", 1, 3),
                ("other", 1, 4),
            ]
            conn.executemany(
                """
                INSERT INTO evidence_types (name, active, sort_order)
                VALUES (?, ?, ?)
                """,
                defaults,
            )
