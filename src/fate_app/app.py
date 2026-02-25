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
    "app.title": "Fate V1",
    "sidebar.navigate": "Navigate",
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
    "term.main": "Main",
    "term.side": "Side",
    "term.yes": "Yes",
    "term.no": "No",
    "option.none": "None",
    "status.none": "None",
    "status.min": "Min",
    "status.normal": "Normal",
    "filter.lines.all": "All",
    "btn.start_25": "推进25’",
    "btn.start_5": "救火5’",
    "btn.save_evidence": "保存证据/完成推进",
    "btn.save_habits": "Save Habits",
    "btn.create_habit": "Create Habit",
    "btn.save_habit": "Save Habit",
    "btn.create_line": "Create Line",
    "btn.save_line": "Save Line",
    "btn.create_quest": "Create Quest",
    "btn.save_quest": "Save Quest",
    "btn.save_review": "Save Review",
    "btn.save_labels": "Save Labels",
    "btn.add_evidence_type": "Add Evidence Type",
    "btn.delete_evidence_type": "Delete Evidence Type",
    "section.habits": "Habits",
    "section.mainline_push": "Mainline Push",
    "section.feedback": "Feedback",
    "section.add_habit": "Add Habit",
    "section.edit_habits": "Edit Habits",
    "section.add_line": "Add Line",
    "section.edit_line": "Edit Line",
    "section.quests": "Quests",
    "section.add_quest": "Add Quest",
    "section.edit_quest": "Edit Quest",
    "section.ui_labels_editor": "UI Labels Editor",
    "field.date": "Date",
    "field.focus_line": "Focus Line",
    "field.minutes": "Minutes",
    "field.evidence_type": "Evidence Type",
    "field.evidence_type_new": "New Evidence Type",
    "field.evidence_text_required": "Evidence Text (required)",
    "field.evidence_ref_required": "Evidence Reference (required)",
    "field.name": "Name",
    "field.group": "Group",
    "field.min_desc": "Min Description",
    "field.normal_desc": "Normal Description",
    "field.min_xp": "Min XP",
    "field.normal_xp": "Normal XP",
    "field.sort_order": "Sort Order",
    "field.active": "Active",
    "field.select_habit": "Select Habit",
    "field.schedule_type": "Schedule Type",
    "field.weekly_days": "Weekly Days",
    "field.interval_days": "Interval Days",
    "field.anchor_date": "Anchor Date",
    "field.cooldown_days": "Cooldown Days",
    "field.filter_lines": "Filter Lines",
    "field.type": "Type",
    "field.ultimate_goal": "Ultimate Goal",
    "field.select_line": "Select Line",
    "field.title": "Title",
    "field.chapter_optional": "Chapter (optional)",
    "field.definition_of_done": "Definition of Done",
    "field.order_index": "Order Index",
    "field.difficulty_range": "Difficulty (1-5)",
    "field.is_boss": "Is Boss",
    "field.select_quest": "Select Quest",
    "field.week_start": "Week Start (Monday)",
    "field.effective": "Effective",
    "field.friction": "Friction",
    "field.next_change": "Next Change",
    "label.next_action": "Next Action",
    "label.progress": "Progress",
    "label.weighted_progress": "Weighted Progress",
    "label.line_progress": "Line Progress",
    "label.chapter_progress": "Chapter Progress",
    "label.uncategorized": "Uncategorized",
    "label.schedule": "Schedule",
    "label.total_habits": "Total Habits",
    "label.total_lines": "Total Lines",
    "label.total_quest_completions": "Total Quest Completions",
    "label.perfect_days_last_7": "Perfect Days (last 7)",
    "label.difficulty": "difficulty",
    "label.boss": "boss",
    "info.habits.empty": "Create your first habit in Consistency.",
    "info.lines.empty": "Create a line in Mainlines to start pushes.",
    "info.no_remaining_quests": "No remaining quests for this line.",
    "info.no_habits": "No habits yet.",
    "info.no_lines": "No lines yet.",
    "info.no_quests": "No quests yet.",
    "msg.habits.saved": "Habits saved.",
    "msg.habit_created": "Habit created.",
    "msg.habit_updated": "Habit updated.",
    "msg.line_created": "Line created.",
    "msg.line_updated": "Line updated.",
    "msg.quest_created": "Quest created.",
    "msg.quest_updated": "Quest updated.",
    "msg.quest_completion_saved": "Quest completion saved.",
    "msg.review_saved": "Review saved.",
    "msg.labels_updated": "Labels updated.",
    "msg.evidence_type_added": "Evidence type added.",
    "msg.evidence_type_deleted": "Evidence type deleted.",
    "error.name_required": "Name is required.",
    "error.title_required": "Title is required.",
    "error.no_quest_available": "No quest available to complete.",
    "error.evidence_type_required": "Evidence type name is required.",
    "error.evidence_type_exists": "Evidence type already exists.",
    "error.evidence_type_delete_none": "Select an evidence type to delete.",
    "schedule.type.always": "Always",
    "schedule.type.weekly": "Weekly",
    "schedule.type.interval": "Interval",
    "schedule.type.cooldown": "Cooldown",
    "weekday.0": "Monday",
    "weekday.1": "Tuesday",
    "weekday.2": "Wednesday",
    "weekday.3": "Thursday",
    "weekday.4": "Friday",
    "weekday.5": "Saturday",
    "weekday.6": "Sunday",
    "evidence.type.none": "",
    "evidence.type.commit": "commit",
    "evidence.type.file": "file",
    "evidence.type.issue": "issue",
    "evidence.type.note": "note",
    "evidence.type.other": "other",
}

SCHEDULE_TYPES = ["always", "weekly", "interval", "cooldown"]
WEEKDAY_OPTIONS = list(range(7))


def label(key: str, default_value: str) -> str:
    return L(key, LABEL_KEYS.get(key, default_value))


def nav_label(page_key: str) -> str:
    label_key, default_value = NAV_KEYS[page_key]
    return label(label_key, default_value)


def group_label(group: str) -> str:
    return label(f"term.{group}", group.title())


def status_label(status: str) -> str:
    return label(f"status.{status}", status.title())


def line_type_label(line_type: str) -> str:
    return label(f"term.{line_type}", line_type.title())


def filter_line_label(filter_value: str) -> str:
    if filter_value == "all":
        return label("filter.lines.all", "All")
    return line_type_label(filter_value)


def yes_no(value: bool) -> str:
    return label("term.yes", "Yes") if value else label("term.no", "No")


def schedule_type_label(schedule_type: str) -> str:
    return label(f"schedule.type.{schedule_type}", schedule_type.title())


def weekday_label(day_idx: int) -> str:
    return label(f"weekday.{day_idx}", str(day_idx))


def parse_weekly_days(raw: str | None) -> list[int]:
    if not raw:
        return []
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    days = []
    for part in parts:
        try:
            day_idx = int(part)
        except ValueError:
            continue
        if 0 <= day_idx <= 6:
            days.append(day_idx)
    return sorted(set(days))


def serialize_weekly_days(days: list[int]) -> str | None:
    if not days:
        return None
    return ",".join(str(day) for day in sorted(set(days)))


def schedule_summary(schedule: dict | None) -> str:
    if not schedule:
        return schedule_type_label("always")
    schedule_type = schedule.get("schedule_type") or "always"
    if schedule_type == "weekly":
        days = parse_weekly_days(schedule.get("weekly_days"))
        if not days:
            return schedule_type_label("weekly")
        day_labels = ", ".join(weekday_label(day) for day in days)
        return f"{schedule_type_label('weekly')}: {day_labels}"
    if schedule_type == "interval":
        interval_days = schedule.get("interval_days")
        anchor_date = schedule.get("anchor_date")
        if interval_days and anchor_date:
            return f"{schedule_type_label('interval')}: {interval_days} @ {anchor_date}"
        if interval_days:
            return f"{schedule_type_label('interval')}: {interval_days}"
    if schedule_type == "cooldown":
        cooldown_days = schedule.get("cooldown_days")
        if cooldown_days:
            return f"{schedule_type_label('cooldown')}: {cooldown_days}"
    return schedule_type_label(schedule_type)


def today_page() -> None:
    st.title(nav_label("today"))
    selected_date = st.date_input(label("field.date", "Date"), value=date_cls.today())
    day_str = selected_date.isoformat()

    habits = rules.list_scheduled_habits(day_str)
    habit_logs = crud.get_habit_logs(day_str, [h["id"] for h in habits])

    st.subheader(label("section.habits", "Habits"))
    if not habits:
        st.info(label("info.habits.empty", "Create your first habit in Consistency."))
    else:
        with st.form("habits_form"):
            for group in ("growth", "health", "maintenance"):
                group_habits = [h for h in habits if h["group"] == group]
                if not group_habits:
                    continue
                st.markdown(f"**{group_label(group)}**")
                for habit in group_habits:
                    default_status = habit_logs.get(habit["id"], {}).get("status", "none")
                    st.selectbox(
                        habit["name"],
                        options=["none", "min", "normal"],
                        index=["none", "min", "normal"].index(default_status),
                        format_func=status_label,
                        key=f"habit_status_{habit['id']}",
                    )
            if st.form_submit_button(label("btn.save_habits", "Save Habits")):
                for habit in habits:
                    status = st.session_state.get(f"habit_status_{habit['id']}", "none")
                    crud.upsert_habit_log(day_str, habit["id"], status, None, None)
                st.success(label("msg.habits.saved", "Habits saved."))
                st.rerun()

    perfect_day = rules.compute_perfect_day(day_str)
    today_streak = rules.compute_streak(date_cls.today().isoformat())
    st.metric(label("term.perfect_day", "Perfect Day"), yes_no(perfect_day))
    st.metric(label("term.streak", "Streak"), today_streak)

    st.subheader(label("section.mainline_push", "Mainline Push"))
    lines = crud.list_lines(active_only=True)
    if not lines:
        st.info(label("info.lines.empty", "Create a line in Mainlines to start pushes."))
    else:
        line_ids = [line["id"] for line in lines]
        stored_focus = crud.get_setting("focus_line_id")
        try:
            stored_focus_id = int(stored_focus) if stored_focus else None
        except ValueError:
            stored_focus_id = None
        default_line_id = stored_focus_id if stored_focus_id in line_ids else line_ids[0]
        selected_line_id = st.selectbox(
            label("field.focus_line", "Focus Line"),
            options=line_ids,
            format_func=lambda lid: next(line["name"] for line in lines if line["id"] == lid),
            index=line_ids.index(default_line_id),
        )
        crud.set_setting("focus_line_id", str(selected_line_id))

        next_quest = rules.get_next_quest(selected_line_id)
        if next_quest:
            st.write(f"**{label('label.next_action', 'Next Action')}:** {next_quest['title']}")
            if next_quest.get("dod"):
                st.caption(next_quest["dod"])
        else:
            st.info(label("info.no_remaining_quests", "No remaining quests for this line."))

        col_25, col_5 = st.columns(2)
        with col_25:
            if st.button(label("btn.start_25", "Start 25’")):
                st.session_state["completion_minutes"] = 25
        with col_5:
            if st.button(label("btn.start_5", "Start 5’")):
                st.session_state["completion_minutes"] = 5

        with st.form("completion_form"):
            minutes = st.number_input(
                label("field.minutes", "Minutes"),
                min_value=1,
                max_value=240,
                value=int(st.session_state.get("completion_minutes", 25)),
                step=1,
            )
            evidence_types = crud.list_evidence_types(active_only=True)
            evidence_type_map = {etype["id"]: etype for etype in evidence_types}
            evidence_type_id = st.selectbox(
                label("field.evidence_type", "Evidence Type"),
                options=[None, *evidence_type_map.keys()],
                format_func=lambda etype_id: (
                    label("option.none", "None")
                    if etype_id is None
                    else evidence_type_map[etype_id]["name"]
                ),
            )
            new_type_name = st.text_input(label("field.evidence_type_new", "New Evidence Type"))
            add_type = st.form_submit_button(label("btn.add_evidence_type", "Add Evidence Type"))
            delete_type = st.form_submit_button(
                label("btn.delete_evidence_type", "Delete Evidence Type")
            )
            evidence_text = st.text_input(
                label("field.evidence_text_required", "Evidence Text (required)")
            )
            evidence_ref = st.text_input(
                label("field.evidence_ref_required", "Evidence Reference (required)")
            )
            save_completion = st.form_submit_button(
                label("btn.save_evidence", "Save Evidence / Complete Push")
            )
            if add_type:
                if not new_type_name.strip():
                    st.error(label("error.evidence_type_required", "Evidence type name is required."))
                else:
                    existing = crud.get_evidence_type_by_name(new_type_name.strip())
                    if existing and existing["active"]:
                        st.error(label("error.evidence_type_exists", "Evidence type already exists."))
                    else:
                        if existing:
                            crud.set_evidence_type_active(existing["id"], 1)
                        else:
                            next_sort = (
                                max((etype["sort_order"] for etype in evidence_types), default=-1) + 1
                            )
                            crud.upsert_evidence_type(new_type_name.strip(), 1, next_sort)
                        st.success(label("msg.evidence_type_added", "Evidence type added."))
                        st.rerun()
            elif delete_type:
                if evidence_type_id is None:
                    st.error(
                        label("error.evidence_type_delete_none", "Select an evidence type to delete.")
                    )
                else:
                    crud.set_evidence_type_active(evidence_type_id, 0)
                    st.success(label("msg.evidence_type_deleted", "Evidence type deleted."))
                    st.rerun()
            elif save_completion:
                if not next_quest:
                    st.error(label("error.no_quest_available", "No quest available to complete."))
                else:
                    evidence_type_name = (
                        evidence_type_map[evidence_type_id]["name"] if evidence_type_id else None
                    )
                    try:
                        crud.create_quest_completion(
                            day_str,
                            next_quest["id"],
                            minutes,
                            evidence_type_name,
                            evidence_text,
                            evidence_ref,
                        )
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        st.success(label("msg.quest_completion_saved", "Quest completion saved."))
                        st.rerun()

        st.subheader(label("section.feedback", "Feedback"))
        effort = rules.compute_effort_xp(day_str)
        st.write(
            f"{label('term.effort_xp', 'Effort XP')}: "
            f"{effort['total']} ("
            f"{label('term.growth', 'Growth')} {effort['growth']}, "
            f"{label('term.health', 'Health')} {effort['health']}, "
            f"{label('term.maintenance', 'Maintenance')} {effort['maintenance']})"
        )
        skill = rules.compute_skill_xp(day_str)
        st.write(f"{label('term.skill_xp', 'Skill XP')}: {skill['total']}")
        for line_id, payload in skill["by_line"].items():
            st.caption(f"{payload['line_name']}: {payload['xp']}")

        completed, total = rules.line_progress(selected_line_id)
        if total > 0:
            st.progress(completed / total)
            st.caption(f"{label('label.progress', 'Progress')}: {completed} / {total}")


def consistency_page() -> None:
    st.title(nav_label("consistency"))
    habits = crud.list_habits(active_only=False)
    schedules = crud.list_habit_schedules([habit["id"] for habit in habits])

    if habits:
        habit_rows = []
        for habit in habits:
            schedule = schedules.get(habit["id"])
            habit_rows.append(
                {
                    label("field.name", "Name"): habit["name"],
                    label("field.group", "Group"): group_label(habit["group"]),
                    label("field.min_desc", "Min Description"): habit.get("min_desc") or "",
                    label("field.normal_desc", "Normal Description"): habit.get("normal_desc") or "",
                    label("field.min_xp", "Min XP"): habit["min_xp"],
                    label("field.normal_xp", "Normal XP"): habit["normal_xp"],
                    label("field.sort_order", "Sort Order"): habit["sort_order"],
                    label("field.active", "Active"): yes_no(bool(habit["active"])),
                    label("label.schedule", "Schedule"): schedule_summary(schedule),
                }
            )
        st.dataframe(habit_rows, use_container_width=True, hide_index=True)
    else:
        st.info(label("info.no_habits", "No habits yet."))

    with st.expander(label("section.add_habit", "Add Habit"), expanded=not habits):
        with st.form("habit_add_form"):
            name = st.text_input(label("field.name", "Name"))
            group = st.selectbox(
                label("field.group", "Group"),
                ["growth", "health", "maintenance"],
                format_func=group_label,
            )
            min_desc = st.text_input(label("field.min_desc", "Min Description"))
            normal_desc = st.text_input(label("field.normal_desc", "Normal Description"))
            min_xp = st.number_input(label("field.min_xp", "Min XP"), min_value=0, value=1, step=1)
            normal_xp = st.number_input(
                label("field.normal_xp", "Normal XP"), min_value=0, value=2, step=1
            )
            sort_order = st.number_input(
                label("field.sort_order", "Sort Order"), min_value=0, value=0, step=1
            )
            active = st.checkbox(label("field.active", "Active"), value=True)
            schedule_type = st.selectbox(
                label("field.schedule_type", "Schedule Type"),
                SCHEDULE_TYPES,
                format_func=schedule_type_label,
            )
            weekly_days = []
            interval_days = None
            anchor_date = None
            cooldown_days = None
            if schedule_type == "weekly":
                weekly_days = st.multiselect(
                    label("field.weekly_days", "Weekly Days"),
                    WEEKDAY_OPTIONS,
                    default=WEEKDAY_OPTIONS,
                    format_func=weekday_label,
                )
            elif schedule_type == "interval":
                interval_days = st.number_input(
                    label("field.interval_days", "Interval Days"),
                    min_value=1,
                    value=1,
                    step=1,
                )
                anchor_date = st.date_input(
                    label("field.anchor_date", "Anchor Date"), value=date_cls.today()
                )
            elif schedule_type == "cooldown":
                cooldown_days = st.number_input(
                    label("field.cooldown_days", "Cooldown Days"),
                    min_value=1,
                    value=1,
                    step=1,
                )
            if st.form_submit_button(label("btn.create_habit", "Create Habit")):
                if not name.strip():
                    st.error(label("error.name_required", "Name is required."))
                else:
                    habit_id = crud.upsert_habit(
                        name.strip(),
                        group,
                        min_desc,
                        normal_desc,
                        int(min_xp),
                        int(normal_xp),
                        1 if active else 0,
                        int(sort_order),
                    )
                    crud.upsert_habit_schedule(
                        habit_id,
                        schedule_type,
                        serialize_weekly_days(weekly_days),
                        int(interval_days) if interval_days else None,
                        anchor_date.isoformat() if anchor_date else None,
                        int(cooldown_days) if cooldown_days else None,
                    )
                    st.success(label("msg.habit_created", "Habit created."))
                    st.rerun()

    if not habits:
        return

    habit_map = {habit["id"]: habit for habit in habits}
    with st.expander(label("section.edit_habits", "Edit Habits")):
        selected_id = st.selectbox(
            label("field.select_habit", "Select Habit"),
            options=list(habit_map.keys()),
            format_func=lambda hid: habit_map[hid]["name"],
        )
        habit = habit_map[selected_id]
        with st.form("habit_edit_form"):
            name = st.text_input(label("field.name", "Name"), value=habit["name"])
            group = st.selectbox(
                label("field.group", "Group"),
                ["growth", "health", "maintenance"],
                index=["growth", "health", "maintenance"].index(habit["group"]),
                format_func=group_label,
            )
            min_desc = st.text_input(
                label("field.min_desc", "Min Description"), value=habit.get("min_desc") or ""
            )
            normal_desc = st.text_input(
                label("field.normal_desc", "Normal Description"),
                value=habit.get("normal_desc") or "",
            )
            min_xp = st.number_input(
                label("field.min_xp", "Min XP"),
                min_value=0,
                value=int(habit["min_xp"]),
                step=1,
            )
            normal_xp = st.number_input(
                label("field.normal_xp", "Normal XP"),
                min_value=0,
                value=int(habit["normal_xp"]),
                step=1,
            )
            sort_order = st.number_input(
                label("field.sort_order", "Sort Order"),
                min_value=0,
                value=int(habit["sort_order"]),
                step=1,
            )
            active = st.checkbox(label("field.active", "Active"), value=bool(habit["active"]))
            schedule = schedules.get(habit["id"], {})
            schedule_type_default = schedule.get("schedule_type") or "always"
            if schedule_type_default not in SCHEDULE_TYPES:
                schedule_type_default = "always"
            schedule_type = st.selectbox(
                label("field.schedule_type", "Schedule Type"),
                SCHEDULE_TYPES,
                index=SCHEDULE_TYPES.index(schedule_type_default),
                format_func=schedule_type_label,
            )
            weekly_days = []
            interval_days = None
            anchor_date = None
            cooldown_days = None
            if schedule_type == "weekly":
                existing_days = parse_weekly_days(schedule.get("weekly_days"))
                weekly_days = st.multiselect(
                    label("field.weekly_days", "Weekly Days"),
                    WEEKDAY_OPTIONS,
                    default=existing_days or WEEKDAY_OPTIONS,
                    format_func=weekday_label,
                )
            elif schedule_type == "interval":
                interval_days = st.number_input(
                    label("field.interval_days", "Interval Days"),
                    min_value=1,
                    value=int(schedule.get("interval_days") or 1),
                    step=1,
                )
                anchor_raw = schedule.get("anchor_date") or habit.get("created_at") or ""
                anchor_str = anchor_raw[:10] if anchor_raw else date_cls.today().isoformat()
                anchor_date = st.date_input(
                    label("field.anchor_date", "Anchor Date"),
                    value=date_cls.fromisoformat(anchor_str),
                )
            elif schedule_type == "cooldown":
                cooldown_days = st.number_input(
                    label("field.cooldown_days", "Cooldown Days"),
                    min_value=1,
                    value=int(schedule.get("cooldown_days") or 1),
                    step=1,
                )
            if st.form_submit_button(label("btn.save_habit", "Save Habit")):
                if not name.strip():
                    st.error(label("error.name_required", "Name is required."))
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
                    crud.upsert_habit_schedule(
                        habit["id"],
                        schedule_type,
                        serialize_weekly_days(weekly_days),
                        int(interval_days) if interval_days else None,
                        anchor_date.isoformat() if anchor_date else None,
                        int(cooldown_days) if cooldown_days else None,
                    )
                    st.success(label("msg.habit_updated", "Habit updated."))
                    st.rerun()


def mainlines_page() -> None:
    st.title(nav_label("mainlines"))
    filter_choice = st.selectbox(
        label("field.filter_lines", "Filter Lines"),
        ["all", "main", "side"],
        format_func=filter_line_label,
    )
    lines = crud.list_lines(active_only=False, line_type=filter_choice)

    if not lines:
        st.info(label("info.no_lines", "No lines yet."))
        with st.expander(label("section.add_line", "Add Line"), expanded=True):
            with st.form("line_add_form"):
                name = st.text_input(label("field.name", "Name"))
                line_type = st.selectbox(
                    label("field.type", "Type"),
                    ["main", "side"],
                    format_func=line_type_label,
                )
                ultimate_goal = st.text_area(label("field.ultimate_goal", "Ultimate Goal"))
                sort_order = st.number_input(
                    label("field.sort_order", "Sort Order"), min_value=0, value=0, step=1
                )
                active = st.checkbox(label("field.active", "Active"), value=True)
                if st.form_submit_button(label("btn.create_line", "Create Line")):
                    if not name.strip():
                        st.error(label("error.name_required", "Name is required."))
                    else:
                        crud.upsert_line(
                            name.strip(),
                            line_type,
                            ultimate_goal,
                            1 if active else 0,
                            int(sort_order),
                        )
                        st.success(label("msg.line_created", "Line created."))
                        st.rerun()
        return

    with st.expander(label("section.add_line", "Add Line"), expanded=False):
        with st.form("line_add_form"):
            name = st.text_input(label("field.name", "Name"))
            line_type = st.selectbox(
                label("field.type", "Type"),
                ["main", "side"],
                format_func=line_type_label,
            )
            ultimate_goal = st.text_area(label("field.ultimate_goal", "Ultimate Goal"))
            sort_order = st.number_input(
                label("field.sort_order", "Sort Order"), min_value=0, value=0, step=1
            )
            active = st.checkbox(label("field.active", "Active"), value=True)
            if st.form_submit_button(label("btn.create_line", "Create Line")):
                if not name.strip():
                    st.error(label("error.name_required", "Name is required."))
                else:
                    crud.upsert_line(
                        name.strip(),
                        line_type,
                        ultimate_goal,
                        1 if active else 0,
                        int(sort_order),
                    )
                    st.success(label("msg.line_created", "Line created."))
                    st.rerun()

    line_map = {line["id"]: line for line in lines}
    selected_line_id = st.selectbox(
        label("field.select_line", "Select Line"),
        options=list(line_map.keys()),
        format_func=lambda lid: line_map[lid]["name"],
    )
    line = line_map[selected_line_id]

    with st.expander(label("section.edit_line", "Edit Line"), expanded=False):
        with st.form("line_edit_form"):
            name = st.text_input(label("field.name", "Name"), value=line["name"])
            line_type = st.selectbox(
                label("field.type", "Type"),
                ["main", "side"],
                index=["main", "side"].index(line["type"]),
                format_func=line_type_label,
            )
            ultimate_goal = st.text_area(
                label("field.ultimate_goal", "Ultimate Goal"),
                value=line.get("ultimate_goal") or "",
            )
            sort_order = st.number_input(
                label("field.sort_order", "Sort Order"),
                min_value=0,
                value=int(line["sort_order"]),
                step=1,
            )
            active = st.checkbox(label("field.active", "Active"), value=bool(line["active"]))
            if st.form_submit_button(label("btn.save_line", "Save Line")):
                if not name.strip():
                    st.error(label("error.name_required", "Name is required."))
                else:
                    crud.upsert_line(
                        name.strip(),
                        line_type,
                        ultimate_goal,
                        1 if active else 0,
                        int(sort_order),
                        line_id=line["id"],
                    )
                    st.success(label("msg.line_updated", "Line updated."))
                    st.rerun()

    st.subheader(label("section.quests", "Quests"))
    quests = crud.list_quests(selected_line_id, active_only=False)
    active_quests = [quest for quest in quests if quest["active"]]

    from fate_core.db import db_connection

    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT qc.quest_id
            FROM quest_completions qc
            JOIN quests q ON q.id = qc.quest_id
            WHERE q.line_id = ?
            """,
            (selected_line_id,),
        ).fetchall()
    completed_ids = {row["quest_id"] for row in rows}

    total_weight = sum(quest["difficulty"] for quest in active_quests)
    completed_weight = sum(
        quest["difficulty"] for quest in active_quests if quest["id"] in completed_ids
    )
    if total_weight > 0:
        st.caption(
            f"{label('label.line_progress', 'Line Progress')} — "
            f"{label('label.weighted_progress', 'Weighted Progress')}: "
            f"{completed_weight} / {total_weight}"
        )
        st.progress(completed_weight / total_weight)

    if quests:
        quests_by_chapter = {}
        for quest in quests:
            chapter = quest.get("chapter") or label("label.uncategorized", "Uncategorized")
            quests_by_chapter.setdefault(chapter, []).append(quest)

        for chapter_name, chapter_quests in quests_by_chapter.items():
            st.markdown(f"**{chapter_name}**")
            chapter_active = [quest for quest in chapter_quests if quest["active"]]
            chapter_total = sum(quest["difficulty"] for quest in chapter_active)
            chapter_completed = sum(
                quest["difficulty"]
                for quest in chapter_active
                if quest["id"] in completed_ids
            )
            if chapter_total > 0:
                st.caption(
                    f"{label('label.chapter_progress', 'Chapter Progress')} — "
                    f"{label('label.weighted_progress', 'Weighted Progress')}: "
                    f"{chapter_completed} / {chapter_total}"
                )
                st.progress(chapter_completed / chapter_total)
            for quest in chapter_quests:
                boss_label = yes_no(bool(quest["is_boss"]))
                active_label = yes_no(bool(quest["active"]))
                st.write(
                    f"{quest['order_idx']}. {quest['title']} "
                    f"({label('label.difficulty', 'difficulty')} {quest['difficulty']}, "
                    f"{label('label.boss', 'boss')}={boss_label}, "
                    f"{label('field.active', 'Active')}={active_label})"
                )
    else:
        st.info(label("info.no_quests", "No quests yet."))

    with st.expander(label("section.add_quest", "Add Quest"), expanded=not quests):
        with st.form("quest_add_form"):
            title = st.text_input(label("field.title", "Title"))
            chapter = st.text_input(label("field.chapter_optional", "Chapter (optional)"))
            dod = st.text_area(label("field.definition_of_done", "Definition of Done"))
            order_idx = st.number_input(
                label("field.order_index", "Order Index"), min_value=1, value=1, step=1
            )
            difficulty = st.number_input(
                label("field.difficulty_range", "Difficulty (1-5)"),
                min_value=1,
                max_value=5,
                value=1,
                step=1,
            )
            is_boss = st.checkbox(label("field.is_boss", "Is Boss"), value=False)
            active = st.checkbox(label("field.active", "Active"), value=True)
            if st.form_submit_button(label("btn.create_quest", "Create Quest")):
                if not title.strip():
                    st.error(label("error.title_required", "Title is required."))
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
                    st.success(label("msg.quest_created", "Quest created."))
                    st.rerun()

    if quests:
        quest_map = {quest["id"]: quest for quest in quests}
        with st.expander(label("section.edit_quest", "Edit Quest"), expanded=False):
            selected_quest_id = st.selectbox(
                label("field.select_quest", "Select Quest"),
                options=list(quest_map.keys()),
                format_func=lambda qid: quest_map[qid]["title"],
            )
            quest = quest_map[selected_quest_id]
            with st.form("quest_edit_form"):
                title = st.text_input(label("field.title", "Title"), value=quest["title"])
                chapter = st.text_input(
                    label("field.chapter_optional", "Chapter (optional)"),
                    value=quest.get("chapter") or "",
                )
                dod = st.text_area(
                    label("field.definition_of_done", "Definition of Done"),
                    value=quest.get("dod") or "",
                )
                order_idx = st.number_input(
                    label("field.order_index", "Order Index"),
                    min_value=1,
                    value=int(quest["order_idx"]),
                    step=1,
                )
                difficulty = st.number_input(
                    label("field.difficulty_range", "Difficulty (1-5)"),
                    min_value=1,
                    max_value=5,
                    value=int(quest["difficulty"]),
                    step=1,
                )
                is_boss = st.checkbox(label("field.is_boss", "Is Boss"), value=bool(quest["is_boss"]))
                active = st.checkbox(label("field.active", "Active"), value=bool(quest["active"]))
                if st.form_submit_button(label("btn.save_quest", "Save Quest")):
                    if not title.strip():
                        st.error(label("error.title_required", "Title is required."))
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
                        st.success(label("msg.quest_updated", "Quest updated."))
                        st.rerun()


def reviews_page() -> None:
    st.title(nav_label("reviews"))
    today = date_cls.today()
    week_start = today - timedelta(days=today.weekday())
    selected_week = st.date_input(
        label("field.week_start", "Week Start (Monday)"), value=week_start
    )
    week_str = selected_week.isoformat()

    existing = crud.get_review_weekly(week_str) or {}
    with st.form("weekly_review_form"):
        effective = st.text_area(
            label("field.effective", "Effective"), value=existing.get("effective", "")
        )
        friction = st.text_area(
            label("field.friction", "Friction"), value=existing.get("friction", "")
        )
        next_change = st.text_area(
            label("field.next_change", "Next Change"), value=existing.get("next_change", "")
        )
        if st.form_submit_button(label("btn.save_review", "Save Review")):
            crud.upsert_review_weekly(week_str, effective, friction, next_change)
            st.success(label("msg.review_saved", "Review saved."))
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
    st.write(f"{label('label.total_habits', 'Total Habits')}: {total_habits}")
    st.write(f"{label('label.total_lines', 'Total Lines')}: {total_lines}")
    st.write(
        f"{label('label.total_quest_completions', 'Total Quest Completions')}: {total_completions}"
    )
    st.write(f"{label('label.perfect_days_last_7', 'Perfect Days (last 7)')}: {last_7}")

    st.subheader(label("section.ui_labels_editor", "UI Labels Editor"))
    stored = list_ui_labels(list(LABEL_KEYS.keys()))
    with st.form("labels_form"):
        updates = {}
        for key, default_value in LABEL_KEYS.items():
            updates[key] = st.text_input(key, value=stored.get(key, default_value))
        if st.form_submit_button(label("btn.save_labels", "Save Labels")):
            for key, value in updates.items():
                upsert_ui_label(key, value)
            st.success(label("msg.labels_updated", "Labels updated."))
            st.rerun()


def main() -> None:
    init_db()
    st.set_page_config(page_title=label("app.title", "Fate V1"), layout="wide")

    st.sidebar.title(label("app.title", "Fate V1"))
    page = st.sidebar.radio(
        label("sidebar.navigate", "Navigate"),
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
