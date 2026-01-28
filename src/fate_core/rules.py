from __future__ import annotations

from datetime import date as date_cls, timedelta

from .db import db_connection

SKILL_XP_BASE = 10


def compute_perfect_day(day: str) -> bool:
    with db_connection() as conn:
        habits = conn.execute(
            "SELECT id FROM habits WHERE active = 1",
        ).fetchall()
        if not habits:
            return False
        habit_ids = [row["id"] for row in habits]
        placeholders = ",".join("?" for _ in habit_ids)
        rows = conn.execute(
            f"""
            SELECT habit_id, status FROM habit_logs
            WHERE date = ? AND habit_id IN ({placeholders})
            """,
            (day, *habit_ids),
        ).fetchall()
    status_by_habit = {row["habit_id"]: row["status"] for row in rows}
    for habit_id in habit_ids:
        status = status_by_habit.get(habit_id)
        if status not in ("min", "normal"):
            return False
    return True


def compute_streak(today: str) -> int:
    current = date_cls.fromisoformat(today)
    streak = 0
    while True:
        if compute_perfect_day(current.isoformat()):
            streak += 1
            current -= timedelta(days=1)
        else:
            break
    return streak


def compute_effort_xp(day: str) -> dict:
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT h."group" AS group_name,
                   hl.status AS status,
                   h.min_xp AS min_xp,
                   h.normal_xp AS normal_xp
            FROM habit_logs hl
            JOIN habits h ON h.id = hl.habit_id
            WHERE hl.date = ?
            """,
            (day,),
        ).fetchall()
    totals: dict[str, int] = {"growth": 0, "health": 0, "maintenance": 0}
    for row in rows:
        if row["status"] == "min":
            totals[row["group_name"]] += int(row["min_xp"] or 0)
        elif row["status"] == "normal":
            totals[row["group_name"]] += int(row["normal_xp"] or 0)
    totals["total"] = sum(totals.values())
    return totals


def compute_skill_xp(day: str) -> dict:
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT l.id AS line_id,
                   l.name AS line_name,
                   q.difficulty AS difficulty
            FROM quest_completions qc
            JOIN quests q ON q.id = qc.quest_id
            JOIN lines l ON l.id = q.line_id
            WHERE qc.date = ?
            """,
            (day,),
        ).fetchall()
    totals: dict[int, dict] = {}
    total_xp = 0
    for row in rows:
        xp = SKILL_XP_BASE * int(row["difficulty"])
        total_xp += xp
        if row["line_id"] not in totals:
            totals[row["line_id"]] = {"line_name": row["line_name"], "xp": 0}
        totals[row["line_id"]]["xp"] += xp
    return {"by_line": totals, "total": total_xp}


def get_next_quest(line_id: int) -> dict | None:
    with db_connection() as conn:
        row = conn.execute(
            """
            SELECT q.*
            FROM quests q
            LEFT JOIN quest_completions qc ON qc.quest_id = q.id
            WHERE q.line_id = ? AND q.active = 1 AND qc.id IS NULL
            ORDER BY q.order_idx ASC, q.id ASC
            LIMIT 1
            """,
            (line_id,),
        ).fetchone()
    return dict(row) if row else None


def line_progress(line_id: int) -> tuple[int, int]:
    with db_connection() as conn:
        total_row = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM quests
            WHERE line_id = ? AND active = 1
            """,
            (line_id,),
        ).fetchone()
        completed_row = conn.execute(
            """
            SELECT COUNT(DISTINCT q.id) AS completed
            FROM quests q
            JOIN quest_completions qc ON qc.quest_id = q.id
            WHERE q.line_id = ? AND q.active = 1
            """,
            (line_id,),
        ).fetchone()
    return int(completed_row["completed"]), int(total_row["total"])


def count_perfect_days_last_n(today: str, days: int) -> int:
    current = date_cls.fromisoformat(today)
    count = 0
    for _ in range(days):
        if compute_perfect_day(current.isoformat()):
            count += 1
        current -= timedelta(days=1)
    return count
