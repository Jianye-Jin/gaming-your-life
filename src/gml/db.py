from __future__ import annotations

import os
import sqlite3
import shutil
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Tuple, Optional

DOMAINS = ("BODY", "MAIN", "HOME", "EXP")


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def default_db_path() -> Path:
    """
    Priority:
    1) env FATE_DB
    2) ~/.fate/fate.db
    """
    p = os.environ.get("FATE_DB")
    if p:
        return Path(p).expanduser()
    return Path("~/.fate/fate.db").expanduser()


def connect(db_path: Optional[Path] = None) -> sqlite3.Connection:
    db_path = (db_path or default_db_path()).expanduser().resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  domain TEXT NOT NULL CHECK(domain IN ('BODY','MAIN','HOME','EXP')),
  cadence TEXT NOT NULL DEFAULT 'daily',
  default_minutes INTEGER NOT NULL DEFAULT 0,
  default_xp INTEGER NOT NULL DEFAULT 0,
  active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  date TEXT NOT NULL,            -- YYYY-MM-DD
  task_id TEXT NOT NULL,
  minutes INTEGER NOT NULL DEFAULT 0,
  xp INTEGER NOT NULL DEFAULT 0,
  notes TEXT NOT NULL DEFAULT '',
  FOREIGN KEY(task_id) REFERENCES tasks(id)
);

CREATE INDEX IF NOT EXISTS idx_logs_date ON logs(date);
CREATE INDEX IF NOT EXISTS idx_logs_task ON logs(task_id);

CREATE TABLE IF NOT EXISTS chests (
  date TEXT PRIMARY KEY,
  eligible INTEGER NOT NULL DEFAULT 0,
  revealed INTEGER NOT NULL DEFAULT 0,
  revealed_ts TEXT
);
"""


def init_db(db_path: Path) -> None:
    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def backup_before_write(db_path: Path) -> None:
    """
    Safety: before we write anything, copy the db to ~/.fate/backups/
    """
    db_path = db_path.expanduser().resolve()
    if not db_path.exists():
        return
    backup_dir = Path("~/.fate/backups").expanduser()
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}_{ts}{db_path.suffix}"
    shutil.copy2(db_path, backup_path)


def seed_tasks_if_empty(db_path: Path) -> None:
    conn = connect(db_path)
    try:
        n = conn.execute("SELECT COUNT(*) AS c FROM tasks;").fetchone()["c"]
        if n:
            return
        rows = [
            ("B001", "Walk 20 min", "BODY", "daily", 20, 0),
            ("M001", "LeetCode 1 problem", "MAIN", "daily", 30, 0),
            ("H001", "Tidy room 10 min", "HOME", "daily", 10, 0),
            ("E001", "English speaking 5 min", "EXP",  "daily", 5, 0),
        ]
        conn.executemany(
            "INSERT INTO tasks(id,name,domain,cadence,default_minutes,default_xp,active,created_at) "
            "VALUES(?,?,?,?,?,?,1,?)",
            [(tid, name, dom, cad, mins, xp, now_ts()) for tid, name, dom, cad, mins, xp in rows],
        )
        conn.commit()
    finally:
        conn.close()


def list_tasks(db_path: Path):
    conn = connect(db_path)
    try:
        return conn.execute(
            "SELECT id, name, domain, cadence, default_minutes, default_xp "
            "FROM tasks WHERE active=1 ORDER BY domain, id;"
        ).fetchall()
    finally:
        conn.close()


def add_task(db_path: Path, tid: str, name: str, domain: str, cadence: str, default_minutes: int, default_xp: int) -> None:
    if domain not in DOMAINS:
        raise ValueError(f"domain must be one of {DOMAINS}")
    conn = connect(db_path)
    try:
        conn.execute(
            "INSERT INTO tasks(id,name,domain,cadence,default_minutes,default_xp,active,created_at) "
            "VALUES(?,?,?,?,?,?,1,?)",
            (tid, name, domain, cadence, int(default_minutes), int(default_xp), now_ts()),
        )
        conn.commit()
    finally:
        conn.close()


def insert_log(db_path: Path, date_str: str, task_id: str, minutes: int, notes: str) -> None:
    conn = connect(db_path)
    try:
        row = conn.execute(
            "SELECT default_xp FROM tasks WHERE id=? AND active=1;",
            (task_id,),
        ).fetchone()
        if not row:
            raise ValueError(f"Unknown/Inactive task_id: {task_id}")
        xp = int(row["default_xp"] or 0)
        conn.execute(
            "INSERT INTO logs(ts,date,task_id,minutes,xp,notes) VALUES(?,?,?,?,?,?)",
            (now_ts(), date_str, task_id, int(minutes), xp, notes or ""),
        )
        conn.commit()
    finally:
        conn.close()


def counts_for_date(db_path: Path, date_str: str) -> Tuple[Dict[str, int], int, int]:
    conn = connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT t.domain AS domain,
                   COUNT(*) AS n,
                   COALESCE(SUM(l.minutes),0) AS mins,
                   COALESCE(SUM(l.xp),0) AS xp
            FROM logs l
            JOIN tasks t ON t.id = l.task_id
            WHERE l.date = ?
            GROUP BY t.domain
            """,
            (date_str,),
        ).fetchall()

        counts = {d: 0 for d in DOMAINS}
        total_mins = 0
        total_xp = 0
        for r in rows:
            d = str(r["domain"])
            counts[d] = int(r["n"])
            total_mins += int(r["mins"])
            total_xp += int(r["xp"])
        return counts, total_mins, total_xp
    finally:
        conn.close()


def mark_chest(db_path: Path, date_str: str, reveal: bool) -> None:
    conn = connect(db_path)
    try:
        conn.execute("INSERT OR IGNORE INTO chests(date, eligible, revealed) VALUES(?,0,0);", (date_str,))
        conn.execute("UPDATE chests SET eligible=1 WHERE date=?;", (date_str,))
        if reveal:
            conn.execute("UPDATE chests SET revealed=1, revealed_ts=? WHERE date=?;", (now_ts(), date_str))
        conn.commit()
    finally:
        conn.close()
