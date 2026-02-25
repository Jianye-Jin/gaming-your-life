from __future__ import annotations

from datetime import date as date_cls, timedelta

from .db import db_connection

SKILL_XP_BASE = 10


def _parse_weekly_days(raw: str | None) -> set[int]:
    if not raw:
        return set()
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    days: set[int] = set()
    for part in parts:
        try:
            day_idx = int(part)
        except ValueError:
            continue
        if 0 <= day_idx <= 6:
            days.add(day_idx)
    return days


def _date_only(value: str | None) -> str | None:
    if not value:
        return None
    return value[:10]


def _is_habit_scheduled(
    habit: dict,
    schedule: dict | None,
    day_date: date_cls,
    last_completion_date: str | None,
) -> bool:
    schedule_type = (schedule or {}).get("schedule_type") or "always"
    if schedule_type == "always":
        return True
    if schedule_type == "weekly":
        days = _parse_weekly_days((schedule or {}).get("weekly_days"))
        if not days:
            return False
        return day_date.weekday() in days
    if schedule_type == "interval":
        interval_days = int((schedule or {}).get("interval_days") or 0)
        if interval_days <= 0:
            return False
        anchor_raw = (schedule or {}).get("anchor_date") or habit.get("created_at")
        anchor_date_str = _date_only(anchor_raw)
        if not anchor_date_str:
            return False
        anchor_date = date_cls.fromisoformat(anchor_date_str)
        delta_days = (day_date - anchor_date).days
        return delta_days >= 0 and delta_days % interval_days == 0
    if schedule_type == "cooldown":
        cooldown_days = int((schedule or {}).get("cooldown_days") or 0)
        if cooldown_days <= 0:
            return True
        if not last_completion_date:
            return True
        last_date = date_cls.fromisoformat(last_completion_date)
        return (day_date - last_date).days > cooldown_days
    return True


def list_scheduled_habits(day: str) -> list[dict]:
    day_date = date_cls.fromisoformat(day)
    with db_connection() as conn:
        habits = conn.execute(
            "SELECT * FROM habits WHERE active = 1",
        ).fetchall()
        if not habits:
            return []
        habit_ids = [row["id"] for row in habits]
        placeholders = ",".join("?" for _ in habit_ids)
        schedule_rows = conn.execute(
            f"""
            SELECT * FROM habit_schedules
            WHERE habit_id IN ({placeholders})
            """,
            tuple(habit_ids),
        ).fetchall()
        last_rows = conn.execute(
            f"""
            SELECT habit_id, MAX(date) AS last_date
            FROM habit_logs
            WHERE habit_id IN ({placeholders})
              AND status IN ('min', 'normal')
              AND date <= ?
            GROUP BY habit_id
            """,
            (*habit_ids, day),
        ).fetchall()
    schedule_map = {row["habit_id"]: dict(row) for row in schedule_rows}
    last_map = {row["habit_id"]: row["last_date"] for row in last_rows}
    scheduled = []
    for habit_row in habits:
        habit = dict(habit_row)
        schedule = schedule_map.get(habit["id"])
        last_completion = last_map.get(habit["id"])
        if _is_habit_scheduled(habit, schedule, day_date, last_completion):
            scheduled.append(habit)
    return scheduled


def compute_perfect_day(day: str) -> bool:
    habits = list_scheduled_habits(day)
    if not habits:
        return False
    habit_ids = [habit["id"] for habit in habits]
    placeholders = ",".join("?" for _ in habit_ids)
    with db_connection() as conn:
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
