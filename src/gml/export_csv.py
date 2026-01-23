from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from gml import db


def export_csv_bundle(
    db_path: Path,
    out_dir: Path,
    since: Optional[str] = None,
    until: Optional[str] = None,
    overwrite: bool = False,
) -> Path:
    """
    Export TASKS / LOG / CHESTS from SQLite into CSV files in a directory.

    Output files:
      - tasks.csv
      - log.csv   (aligned with your LOG sheet header)
      - chests.csv

    since/until: filter by date (YYYY-MM-DD), inclusive.
    """
    db_path = db_path.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    def ensure_not_exists(p: Path):
        if p.exists() and not overwrite:
            raise SystemExit(f"Output exists: {p}\nUse --overwrite or choose another --out-dir.")

    tasks_csv = out_dir / "tasks.csv"
    log_csv = out_dir / "log.csv"
    chests_csv = out_dir / "chests.csv"

    ensure_not_exists(tasks_csv)
    ensure_not_exists(log_csv)
    ensure_not_exists(chests_csv)

    conn = db.connect(db_path)
    try:
        # TASKS
        tasks = conn.execute(
            """
            SELECT id, name, domain, cadence, default_minutes, default_xp, active, created_at
            FROM tasks
            ORDER BY domain, id
            """
        ).fetchall()

        # LOG (joined)
        where = []
        params = []
        if since:
            where.append("l.date >= ?")
            params.append(since)
        if until:
            where.append("l.date <= ?")
            params.append(until)
        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        logs = conn.execute(
            f"""
            SELECT
              l.ts       AS timestamp,
              l.date     AS date,
              l.task_id  AS task_id,
              t.name     AS task_name,
              t.domain   AS domain,
              l.minutes  AS minutes,
              l.xp       AS xp,
              l.notes    AS notes
            FROM logs l
            JOIN tasks t ON t.id = l.task_id
            {where_sql}
            ORDER BY l.date, l.ts, l.id
            """,
            params,
        ).fetchall()

        # CHESTS
        c_where = []
        c_params = []
        if since:
            c_where.append("date >= ?")
            c_params.append(since)
        if until:
            c_where.append("date <= ?")
            c_params.append(until)
        c_where_sql = ("WHERE " + " AND ".join(c_where)) if c_where else ""

        chests = conn.execute(
            f"""
            SELECT date, eligible, revealed, revealed_ts
            FROM chests
            {c_where_sql}
            ORDER BY date
            """,
            c_params,
        ).fetchall()

    finally:
        conn.close()

    # Write tasks.csv
    with tasks_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "domain", "cadence", "default_minutes", "default_xp", "active", "created_at"])
        for r in tasks:
            w.writerow([r["id"], r["name"], r["domain"], r["cadence"], r["default_minutes"], r["default_xp"], r["active"], r["created_at"]])

    # Write log.csv (match your LOG sheet header)
    with log_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "date", "task_id", "task_name", "domain", "minutes", "xp", "notes"])
        for r in logs:
            w.writerow([r["timestamp"], r["date"], r["task_id"], r["task_name"], r["domain"], r["minutes"], r["xp"], r["notes"]])

    # Write chests.csv
    with chests_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "eligible", "revealed", "revealed_ts"])
        for r in chests:
            w.writerow([r["date"], r["eligible"], r["revealed"], r["revealed_ts"]])

    return out_dir

