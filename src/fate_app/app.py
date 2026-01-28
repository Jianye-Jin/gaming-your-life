from __future__ import annotations

from datetime import date as date_cls, timedelta

import streamlit as st

from fate_core import init_db
from fate_core import crud, rules
from fate_core.labels import L, list_ui_labels, upsert_ui_label

NAV_KEYS = {
    "today": ("nav.today", "Today"),
    "consistency": ("nav.consistency", "Consistency"),
    "mainlines": ("nav.mainlines", "Mainlines"),
    "reviews": ("nav.reviews", "Reviews"),
    "dashboard": ("nav.dashboard", "Dashboard"),
}

LABEL_KEYS = {
    "nav.today": "Today",
    "nav.consistency": "Consistency",
    "nav.mainlines": "Mainlines",
    "nav.reviews": "Reviews",
    "nav.dashboard": "Dashboard",
    "term.perfect_day": "完美的一天",
    "term.streak": "连胜",
    "term.effort_xp": "努力经验",
    "term.skill_xp": "能力经验",
    "term.growth": "Growth",
    "term.health": "Health",
    "term.maintenance": "Maintenance",
    "btn.start_25": "推进25’",
    "btn.start_5": "救火5’",
    "btn.save_evidence": "保存证据/完成推进",
}

EVIDENCE_TYPES = ["", "commit", "file", "issue", "note", "other"]


def label(key: str, default_value: str) -> str:
    return L(key, default_value)


def nav_label(page_key: str) -> str:
    label_key, default_value = NAV_KEYS[page_key]
    return label(label_key, default_value)


def today_page() -> None:
    st.title(nav_label("today"))
    selected_date = st.date_input("Date", value=date_cls.today())
    day_str = selected_date.isoformat()

    habits = crud.list_habits(active_only=True)
    habit_logs = crud.get_habit_logs(day_str, [h["id"] for h in habits])

    st.subheader("Habits")
    if not habits:
        st.info("Create your first habit in Consistency.")
    else:
        with st.form("habits_form"):
            for group in ("growth", "health", "maintenance"):
                group_habits = [h for h in habits if h["group"] == group]
                if not group_habits:
                    continue
                st.markdown(f"**{label(f'term.{group}', group.title())}**")
                for habit in group_habits:
                    default_status = habit_logs.get(habit["id"], {}).get("status", "none")
                    st.selectbox(
                        habit["name"],
                        options=["none", "min", "normal"],
                        index=["none", "min", "normal"].index(default_status),
                        key=f"habit_status_{habit['id']}",
                    )
            if st.form_submit_button("Save Habits"):
                for habit in habits:
                    status = st.session_state.get(f"habit_status_{habit['id']}", "none")
                    crud.upsert_habit_log(day_str, habit["id"], status, None, None)
                st.success("Habits saved.")
                st.rerun()

    perfect_day = rules.compute_perfect_day(day_str)
    today_streak = rules.compute_streak(date_cls.today().isoformat())
    st.metric(label("term.perfect_day", "Perfect Day"), "Yes" if perfect_day else "No")
    st.metric(label("term.streak", "Streak"), today_streak)

    st.subheader("Mainline Push")
    lines = crud.list_lines(active_only=True)
    if not lines:
        st.info("Create a line in Mainlines to start pushes.")
    else:
        line_ids = [line["id"] for line in lines]
        stored_focus = crud.get_setting("focus_line_id")
        try:
            stored_focus_id = int(stored_focus) if stored_focus else None
        except ValueError:
            stored_focus_id = None
        default_line_id = stored_focus_id if stored_focus_id in line_ids else line_ids[0]
        selected_line_id = st.selectbox(
            "Focus Line",
            options=line_ids,
            format_func=lambda lid: next(line["name"] for line in lines if line["id"] == lid),
            index=line_ids.index(default_line_id),
        )
        crud.set_setting("focus_line_id", str(selected_line_id))

        next_quest = rules.get_next_quest(selected_line_id)
        if next_quest:
            st.write(f"**Next Action:** {next_quest['title']}")
            if next_quest.get("dod"):
                st.caption(next_quest["dod"])
        else:
            st.info("No remaining quests for this line.")

        col_25, col_5 = st.columns(2)
        with col_25:
            if st.button(label("btn.start_25", "Start 25’")):
                st.session_state["completion_minutes"] = 25
        with col_5:
            if st.button(label("btn.start_5", "Start 5’")):
                st.session_state["completion_minutes"] = 5

        with st.form("completion_form"):
            minutes = st.number_input(
                "Minutes",
                min_value=1,
                max_value=240,
                value=int(st.session_state.get("completion_minutes", 25)),
                step=1,
            )
            evidence_type = st.selectbox("Evidence Type", EVIDENCE_TYPES)
            evidence_text = st.text_input("Evidence Text (required)")
            evidence_ref = st.text_input("Evidence Reference (required)")
            if st.form_submit_button(label("btn.save_evidence", "Save Evidence / Complete Push")):
                if not next_quest:
                    st.error("No quest available to complete.")
                else:
                    try:
                        crud.create_quest_completion(
                            day_str,
                            next_quest["id"],
                            minutes,
                            evidence_type or None,
                            evidence_text,
                            evidence_ref,
                        )
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        st.success("Quest completion saved.")
                        st.rerun()

        st.subheader("Feedback")
        effort = rules.compute_effort_xp(day_str)
        st.write(
            f"{label('term.effort_xp', 'Effort XP')}: "
            f"{effort['total']} ("
            f"{label('term.growth','Growth')} {effort['growth']}, "
            f"{label('term.health','Health')} {effort['health']}, "
            f"{label('term.maintenance','Maintenance')} {effort['maintenance']})"
        )
        skill = rules.compute_skill_xp(day_str)
        st.write(f"{label('term.skill_xp', 'Skill XP')}: {skill['total']}")
        for line_id, payload in skill["by_line"].items():
            st.caption(f"{payload['line_name']}: {payload['xp']}")

        completed, total = rules.line_progress(selected_line_id)
        if total > 0:
            st.progress(completed / total)
            st.caption(f"Progress: {completed} / {total}")


def consistency_page() -> None:
    st.title(nav_label("consistency"))
    habits = crud.list_habits(active_only=False)

    st.subheader("Add Habit")
    with st.form("habit_add_form"):
        name = st.text_input("Name")
        group = st.selectbox("Group", ["growth", "health", "maintenance"])
        min_desc = st.text_input("Min Description")
        normal_desc = st.text_input("Normal Description")
        min_xp = st.number_input("Min XP", min_value=0, value=1, step=1)
        normal_xp = st.number_input("Normal XP", min_value=0, value=2, step=1)
        sort_order = st.number_input("Sort Order", min_value=0, value=0, step=1)
        active = st.checkbox("Active", value=True)
        if st.form_submit_button("Create Habit"):
            if not name.strip():
                st.error("Name is required.")
            else:
                crud.upsert_habit(
                    name.strip(),
                    group,
                    min_desc,
                    normal_desc,
                    int(min_xp),
                    int(normal_xp),
                    1 if active else 0,
                    int(sort_order),
                )
                st.success("Habit created.")
                st.rerun()

    st.subheader("Edit Habits")
    if not habits:
        st.info("No habits yet.")
        return

    habit_map = {habit["id"]: habit for habit in habits}
    selected_id = st.selectbox(
        "Select Habit",
        options=list(habit_map.keys()),
        format_func=lambda hid: habit_map[hid]["name"],
    )
    habit = habit_map[selected_id]
    with st.form("habit_edit_form"):
        name = st.text_input("Name", value=habit["name"])
        group = st.selectbox(
            "Group",
            ["growth", "health", "maintenance"],
            index=["growth", "health", "maintenance"].index(habit["group"]),
        )
        min_desc = st.text_input("Min Description", value=habit.get("min_desc") or "")
        normal_desc = st.text_input("Normal Description", value=habit.get("normal_desc") or "")
        min_xp = st.number_input("Min XP", min_value=0, value=int(habit["min_xp"]), step=1)
        normal_xp = st.number_input("Normal XP", min_value=0, value=int(habit["normal_xp"]), step=1)
        sort_order = st.number_input("Sort Order", min_value=0, value=int(habit["sort_order"]), step=1)
        active = st.checkbox("Active", value=bool(habit["active"]))
        if st.form_submit_button("Save Habit"):
            if not name.strip():
                st.error("Name is required.")
            else:
                crud.upsert_habit(
                    name.strip(),
                    group,
                    min_desc,
                    normal_desc,
                    int(min_xp),
                    int(normal_xp),
                    1 if active else 0,
                    int(sort_order),
                    habit_id=habit["id"],
                )
                st.success("Habit updated.")
                st.rerun()


def mainlines_page() -> None:
    st.title(nav_label("mainlines"))
    filter_choice = st.selectbox("Filter Lines", ["all", "main", "side"])
    lines = crud.list_lines(active_only=False, line_type=filter_choice)

    st.subheader("Add Line")
    with st.form("line_add_form"):
        name = st.text_input("Name")
        line_type = st.selectbox("Type", ["main", "side"])
        ultimate_goal = st.text_area("Ultimate Goal")
        sort_order = st.number_input("Sort Order", min_value=0, value=0, step=1)
        active = st.checkbox("Active", value=True)
        if st.form_submit_button("Create Line"):
            if not name.strip():
                st.error("Name is required.")
            else:
                crud.upsert_line(
                    name.strip(),
                    line_type,
                    ultimate_goal,
                    1 if active else 0,
                    int(sort_order),
                )
                st.success("Line created.")
                st.rerun()

    if not lines:
        st.info("No lines yet.")
        return

    line_map = {line["id"]: line for line in lines}
    selected_line_id = st.selectbox(
        "Select Line",
        options=list(line_map.keys()),
        format_func=lambda lid: line_map[lid]["name"],
    )
    line = line_map[selected_line_id]

    st.subheader("Edit Line")
    with st.form("line_edit_form"):
        name = st.text_input("Name", value=line["name"])
        line_type = st.selectbox("Type", ["main", "side"], index=["main", "side"].index(line["type"]))
        ultimate_goal = st.text_area("Ultimate Goal", value=line.get("ultimate_goal") or "")
        sort_order = st.number_input("Sort Order", min_value=0, value=int(line["sort_order"]), step=1)
        active = st.checkbox("Active", value=bool(line["active"]))
        if st.form_submit_button("Save Line"):
            if not name.strip():
                st.error("Name is required.")
            else:
                crud.upsert_line(
                    name.strip(),
                    line_type,
                    ultimate_goal,
                    1 if active else 0,
                    int(sort_order),
                    line_id=line["id"],
                )
                st.success("Line updated.")
                st.rerun()

    st.subheader("Quests")
    quests = crud.list_quests(selected_line_id, active_only=False)
    if quests:
        for quest in quests:
            completed, total = rules.line_progress(selected_line_id)
            st.write(
                f"{quest['order_idx']}. {quest['title']} "
                f"(difficulty {quest['difficulty']}, boss={quest['is_boss']})"
            )
        st.caption(f"Progress: {completed} / {total}")
    else:
        st.info("No quests yet.")

    st.subheader("Add Quest")
    with st.form("quest_add_form"):
        title = st.text_input("Title")
        chapter = st.text_input("Chapter (optional)")
        dod = st.text_area("Definition of Done")
        order_idx = st.number_input("Order Index", min_value=1, value=1, step=1)
        difficulty = st.number_input("Difficulty (1-5)", min_value=1, max_value=5, value=1, step=1)
        is_boss = st.checkbox("Is Boss", value=False)
        active = st.checkbox("Active", value=True)
        if st.form_submit_button("Create Quest"):
            if not title.strip():
                st.error("Title is required.")
            else:
                crud.upsert_quest(
                    selected_line_id,
                    chapter or None,
                    int(order_idx),
                    title.strip(),
                    dod,
                    int(difficulty),
                    1 if is_boss else 0,
                    1 if active else 0,
                )
                st.success("Quest created.")
                st.rerun()

    st.subheader("Edit Quest")
    if quests:
        quest_map = {quest["id"]: quest for quest in quests}
        selected_quest_id = st.selectbox(
            "Select Quest",
            options=list(quest_map.keys()),
            format_func=lambda qid: quest_map[qid]["title"],
        )
        quest = quest_map[selected_quest_id]
        with st.form("quest_edit_form"):
            title = st.text_input("Title", value=quest["title"])
            chapter = st.text_input("Chapter (optional)", value=quest.get("chapter") or "")
            dod = st.text_area("Definition of Done", value=quest.get("dod") or "")
            order_idx = st.number_input("Order Index", min_value=1, value=int(quest["order_idx"]), step=1)
            difficulty = st.number_input(
                "Difficulty (1-5)",
                min_value=1,
                max_value=5,
                value=int(quest["difficulty"]),
                step=1,
            )
            is_boss = st.checkbox("Is Boss", value=bool(quest["is_boss"]))
            active = st.checkbox("Active", value=bool(quest["active"]))
            if st.form_submit_button("Save Quest"):
                if not title.strip():
                    st.error("Title is required.")
                else:
                    crud.upsert_quest(
                        selected_line_id,
                        chapter or None,
                        int(order_idx),
                        title.strip(),
                        dod,
                        int(difficulty),
                        1 if is_boss else 0,
                        1 if active else 0,
                        quest_id=quest["id"],
                    )
                    st.success("Quest updated.")
                    st.rerun()


def reviews_page() -> None:
    st.title(nav_label("reviews"))
    today = date_cls.today()
    week_start = today - timedelta(days=today.weekday())
    selected_week = st.date_input("Week Start (Monday)", value=week_start)
    week_str = selected_week.isoformat()

    existing = crud.get_review_weekly(week_str) or {}
    with st.form("weekly_review_form"):
        effective = st.text_area("Effective", value=existing.get("effective", ""))
        friction = st.text_area("Friction", value=existing.get("friction", ""))
        next_change = st.text_area("Next Change", value=existing.get("next_change", ""))
        if st.form_submit_button("Save Review"):
            crud.upsert_review_weekly(week_str, effective, friction, next_change)
            st.success("Review saved.")
            st.rerun()


def dashboard_page() -> None:
    st.title(nav_label("dashboard"))
    today_str = date_cls.today().isoformat()

    from fate_core.db import db_connection

    with db_connection() as conn:
        total_habits = conn.execute("SELECT COUNT(*) AS c FROM habits").fetchone()["c"]
        total_lines = conn.execute("SELECT COUNT(*) AS c FROM lines").fetchone()["c"]
        total_completions = conn.execute("SELECT COUNT(*) AS c FROM quest_completions").fetchone()["c"]
    streak = rules.compute_streak(today_str)
    last_7 = rules.count_perfect_days_last_n(today_str, 7)

    st.metric(label("term.streak", "Streak"), streak)
    st.write(f"Total Habits: {total_habits}")
    st.write(f"Total Lines: {total_lines}")
    st.write(f"Total Quest Completions: {total_completions}")
    st.write(f"Perfect Days (last 7): {last_7}")

    st.subheader("UI Labels Editor")
    stored = list_ui_labels(list(LABEL_KEYS.keys()))
    with st.form("labels_form"):
        updates = {}
        for key, default_value in LABEL_KEYS.items():
            updates[key] = st.text_input(key, value=stored.get(key, default_value))
        if st.form_submit_button("Save Labels"):
            for key, value in updates.items():
                upsert_ui_label(key, value)
            st.success("Labels updated.")
            st.rerun()


def main() -> None:
    st.set_page_config(page_title="Fate V1", layout="wide")
    init_db()

    st.sidebar.title("Fate V1")
    page = st.sidebar.radio(
        "Navigate",
        options=list(NAV_KEYS.keys()),
        format_func=nav_label,
    )

    if page == "today":
        today_page()
    elif page == "consistency":
        consistency_page()
    elif page == "mainlines":
        mainlines_page()
    elif page == "reviews":
        reviews_page()
    elif page == "dashboard":
        dashboard_page()


if __name__ == "__main__":
    main()
