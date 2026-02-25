from __future__ import annotations

from typing import Iterable

from .db import db_connection


def list_habits(active_only: bool = False) -> list[dict]:
    clause = "WHERE active = 1" if active_only else ""
    with db_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM habits
            {clause}
            ORDER BY sort_order ASC, id ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def upsert_habit(
    name: str,
    group: str,
    min_desc: str,
    normal_desc: str,
    min_xp: int,
    normal_xp: int,
    active: int,
    sort_order: int,
    habit_id: int | None = None,
) -> int:
    with db_connection() as conn:
        if habit_id is None:
            cur = conn.execute(
                """
                INSERT INTO habits (name, "group", min_desc, normal_desc, min_xp, normal_xp, active, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, group, min_desc, normal_desc, min_xp, normal_xp, active, sort_order),
            )
            return int(cur.lastrowid)
        conn.execute(
            """
            UPDATE habits
            SET name = ?, "group" = ?, min_desc = ?, normal_desc = ?, min_xp = ?, normal_xp = ?,
                active = ?, sort_order = ?
            WHERE id = ?
            """,
            (name, group, min_desc, normal_desc, min_xp, normal_xp, active, sort_order, habit_id),
        )
        return habit_id


def set_habit_active(habit_id: int, active: int) -> None:
    with db_connection() as conn:
        conn.execute("UPDATE habits SET active = ? WHERE id = ?", (active, habit_id))


def upsert_habit_log(date: str, habit_id: int, status: str, minutes: int | None, note: str | None) -> None:
    with db_connection() as conn:
        conn.execute(
            """
            INSERT INTO habit_logs (date, habit_id, status, minutes, note)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(date, habit_id)
            DO UPDATE SET status = excluded.status, minutes = excluded.minutes, note = excluded.note
            """,
            (date, habit_id, status, minutes, note),
        )


def get_habit_logs(date: str, habit_ids: Iterable[int]) -> dict[int, dict]:
    habit_ids = list(habit_ids)
    if not habit_ids:
        return {}
    placeholders = ",".join("?" for _ in habit_ids)
    with db_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM habit_logs
            WHERE date = ? AND habit_id IN ({placeholders})
            """,
            (date, *habit_ids),
        ).fetchall()
    return {row["habit_id"]: dict(row) for row in rows}


def list_habit_schedules(habit_ids: Iterable[int]) -> dict[int, dict]:
    habit_ids = list(habit_ids)
    if not habit_ids:
        return {}
    placeholders = ",".join("?" for _ in habit_ids)
    with db_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM habit_schedules
            WHERE habit_id IN ({placeholders})
            """,
            tuple(habit_ids),
        ).fetchall()
    return {row["habit_id"]: dict(row) for row in rows}


def upsert_habit_schedule(
    habit_id: int,
    schedule_type: str,
    weekly_days: str | None,
    interval_days: int | None,
    anchor_date: str | None,
    cooldown_days: int | None,
) -> None:
    with db_connection() as conn:
        conn.execute(
            """
            INSERT INTO habit_schedules
                (habit_id, schedule_type, weekly_days, interval_days, anchor_date, cooldown_days)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(habit_id) DO UPDATE SET
                schedule_type = excluded.schedule_type,
                weekly_days = excluded.weekly_days,
                interval_days = excluded.interval_days,
                anchor_date = excluded.anchor_date,
                cooldown_days = excluded.cooldown_days
            """,
            (habit_id, schedule_type, weekly_days, interval_days, anchor_date, cooldown_days),
        )


def list_lines(active_only: bool = False, line_type: str | None = None) -> list[dict]:
    clauses = []
    params: list = []
    if active_only:
        clauses.append("active = 1")
    if line_type and line_type != "all":
        clauses.append("type = ?")
        params.append(line_type)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    with db_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM lines
            {where}
            ORDER BY sort_order ASC, id ASC
            """,
            tuple(params),
        ).fetchall()
    return [dict(row) for row in rows]


def upsert_line(
    name: str,
    line_type: str,
    ultimate_goal: str,
    active: int,
    sort_order: int,
    line_id: int | None = None,
) -> int:
    with db_connection() as conn:
        if line_id is None:
            cur = conn.execute(
                """
                INSERT INTO lines (name, type, ultimate_goal, active, sort_order)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, line_type, ultimate_goal, active, sort_order),
            )
            return int(cur.lastrowid)
        conn.execute(
            """
            UPDATE lines
            SET name = ?, type = ?, ultimate_goal = ?, active = ?, sort_order = ?
            WHERE id = ?
            """,
            (name, line_type, ultimate_goal, active, sort_order, line_id),
        )
        return line_id


def set_line_active(line_id: int, active: int) -> None:
    with db_connection() as conn:
        conn.execute("UPDATE lines SET active = ? WHERE id = ?", (active, line_id))


def list_quests(line_id: int, active_only: bool = False) -> list[dict]:
    clause = "AND active = 1" if active_only else ""
    with db_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM quests
            WHERE line_id = ?
            {clause}
            ORDER BY order_idx ASC, id ASC
            """,
            (line_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def upsert_quest(
    line_id: int,
    chapter: str | None,
    order_idx: int,
    title: str,
    dod: str,
    difficulty: int,
    is_boss: int,
    active: int,
    quest_id: int | None = None,
) -> int:
    with db_connection() as conn:
        if quest_id is None:
            cur = conn.execute(
                """
                INSERT INTO quests (line_id, chapter, order_idx, title, dod, difficulty, is_boss, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (line_id, chapter, order_idx, title, dod, difficulty, is_boss, active),
            )
            return int(cur.lastrowid)
        conn.execute(
            """
            UPDATE quests
            SET chapter = ?, order_idx = ?, title = ?, dod = ?, difficulty = ?, is_boss = ?, active = ?
            WHERE id = ?
            """,
            (chapter, order_idx, title, dod, difficulty, is_boss, active, quest_id),
        )
        return quest_id


def set_quest_active(quest_id: int, active: int) -> None:
    with db_connection() as conn:
        conn.execute("UPDATE quests SET active = ? WHERE id = ?", (active, quest_id))


def create_quest_completion(
    date: str,
    quest_id: int,
    minutes: int | None,
    evidence_type: str | None,
    evidence_text: str,
    evidence_ref: str,
) -> int:
    if not evidence_text.strip() or not evidence_ref.strip():
        raise ValueError("Evidence text and reference are required.")
    with db_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO quest_completions
                (date, quest_id, minutes, evidence_type, evidence_text, evidence_ref)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (date, quest_id, minutes, evidence_type, evidence_text, evidence_ref),
        )
        return int(cur.lastrowid)


def list_quest_completions(date: str | None = None) -> list[dict]:
    where = "WHERE date = ?" if date else ""
    params = (date,) if date else ()
    with db_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM quest_completions {where} ORDER BY created_at DESC",
            params,
        ).fetchall()
    return [dict(row) for row in rows]


def list_evidence_types(active_only: bool = True) -> list[dict]:
    clause = "WHERE active = 1" if active_only else ""
    with db_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT * FROM evidence_types
            {clause}
            ORDER BY sort_order ASC, id ASC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_evidence_type_by_name(name: str) -> dict | None:
    with db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM evidence_types WHERE LOWER(name) = LOWER(?)",
            (name,),
        ).fetchone()
    return dict(row) if row else None


def upsert_evidence_type(
    name: str,
    active: int,
    sort_order: int,
    evidence_type_id: int | None = None,
) -> int:
    with db_connection() as conn:
        if evidence_type_id is None:
            cur = conn.execute(
                """
                INSERT INTO evidence_types (name, active, sort_order)
                VALUES (?, ?, ?)
                """,
                (name, active, sort_order),
            )
            return int(cur.lastrowid)
        conn.execute(
            """
            UPDATE evidence_types
            SET name = ?, active = ?, sort_order = ?
            WHERE id = ?
            """,
            (name, active, sort_order, evidence_type_id),
        )
        return evidence_type_id


def set_evidence_type_active(evidence_type_id: int, active: int) -> None:
    with db_connection() as conn:
        conn.execute("UPDATE evidence_types SET active = ? WHERE id = ?", (active, evidence_type_id))


def upsert_review_weekly(week_start: str, effective: str, friction: str, next_change: str) -> None:
    with db_connection() as conn:
        conn.execute(
            """
            INSERT INTO reviews_weekly (week_start, effective, friction, next_change)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(week_start)
            DO UPDATE SET effective = excluded.effective,
                          friction = excluded.friction,
                          next_change = excluded.next_change
            """,
            (week_start, effective, friction, next_change),
        )


def get_review_weekly(week_start: str) -> dict | None:
    with db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM reviews_weekly WHERE week_start = ?",
            (week_start,),
        ).fetchone()
    return dict(row) if row else None


def set_setting(key: str, value: str) -> None:
    with db_connection() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )


def get_setting(key: str) -> str | None:
    with db_connection() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None
