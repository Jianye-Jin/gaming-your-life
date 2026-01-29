# Dark-Code / Fate V1 — Codex PRD（Final）

## 0) One-line Goal
- Build a local, single-user growth system app (no network) where the user completes a daily loop on Today:
- Habits → Mainline push → Evidence → Feedback**, with all data stored in SQLite for future upgrades.

## 1) Scope (V1 Must-have)

### Navigation (5 pages)
- Today
- Consistency
- Mainlines
- Reviews
- Dashboard

**Important:** Do NOT rely on Streamlit’s default multipage `pages/` navigation labels. Implement a **custom sidebar router** (e.g., `st.sidebar.radio`) so navigation titles are **label-configurable**.

### V1 Pages

#### (1) Today — Daily loop hub (must be fully working)

- Habits card: grouped into **Growth / Health / Maintenance**
- Each habit has 3 states: `none / min / normal`
- **Perfect Day** status: only true if **ALL active habits** are at least `min` on that date
- **Streak**: consecutive Perfect Days up to today
- Mainline Push card:

  * choose a Focus line (default last used)
  * show Next Action (next incomplete quest)
  * buttons: “25’ push” and “5’ rescue”
* Evidence (required to complete a quest):

  * evidence_text (one sentence)
  * evidence_ref (verifiable reference: problem # / filename / commit hash / etc.)
  * optional evidence_type (dropdown)
* Feedback card:

  * Effort XP (by habit group + total)
  * Skill XP (by line + total)
  * streak value
  * Focus line progress bar (completed quests / total)

#### (2) Consistency — habits + lowest deliverables (basic CRUD)

* Create/edit/disable habits
* Habit fields:

  * group (growth/health/maintenance)
  * min_desc, normal_desc
  * XP config (min_xp, normal_xp)
  * active toggle
  * sort order

#### (3) Mainlines — main/side lines + quests (must support “level-up feeling”)

* Lines list: type = `main` or `side`, can create/edit/disable
* For each line:

  * ultimate_goal (text)
  * quests CRUD with:

    * title
    * DoD (definition of done, measurable/verifiable)
    * difficulty (1–5)
    * is_boss (0/1)
    * order_idx
    * optional chapter (text)
* Show line progress: completed quests / total quests
* Next Action rule: smallest `order_idx` among incomplete quests for that line

#### (4) Reviews — minimal weekly review (not empty)

* Weekly review record (week_start date)
* three text fields:

  * effective
  * friction
  * next_change
* Optional: show weekly stats summary on the same page

#### (5) Dashboard — placeholder + DB summary

* V1: can be simple, but must show at least:

  * current streak
  * total habits / total lines / total quest completions
  * optionally last 7 days perfect-day count

## 2) Non-goals (V1 Not required)

* Cloud sync, multi-user accounts
* Automated health data ingestion
* Complex achievements shop/rewards economy
* Attachments upload/storage (only text references)
* Resource library management (links/materials)
* Advanced analytics beyond simple summaries

---

## 3) Critical Requirement: Rename-safe & Label-configurable UI

### 3.1 Rename-safe (no logic depends on names)

* Business logic (streak, XP, progress, Next Action) must NOT depend on any display strings like habit.name, quest.title, line.name.
* All relations must use stable IDs:

  * habit_logs.habit_id
  * quests.line_id
  * quest_completions.quest_id

### 3.2 Label system (user-editable UI wording)

Implement a label override system so the user can change UI-visible names (navigation titles, key terms, button text) without affecting logic.

* Add table `ui_labels(key TEXT PRIMARY KEY, value TEXT NOT NULL)`
* Implement helper `L(key, default_value)`:

  * if key exists in ui_labels: use stored value
  * else: return default_value
* Add a simple Settings panel (can live in Dashboard or Reviews if you don’t want a 6th nav item):

  * list a predefined set of keys with input boxes
  * save changes to ui_labels

**Must support at least these keys:**

* Navigation:

  * `nav.today` (default "Today")
  * `nav.consistency`
  * `nav.mainlines`
  * `nav.reviews`
  * `nav.dashboard`
* Core terms:

  * `term.perfect_day` (default "完美的一天")
  * `term.streak` (default "连胜")
  * `term.effort_xp` (default "努力经验")
  * `term.skill_xp` (default "能力经验")
  * `term.growth` (default "Growth")
  * `term.health`
  * `term.maintenance`
* Today buttons:

  * `btn.start_25` (default "推进25’")
  * `btn.start_5` (default "救火5’")
  * `btn.save_evidence` (default "保存证据/完成推进")

**Acceptance for labels:**

* Editing `term.perfect_day` updates displayed wording immediately and does not change any stats.
* Editing nav labels changes sidebar text but routing still works.

---

## 4) Core Rules (Business Logic)

### 4.1 Perfect Day

For date D:

* Let active habits = all habits where `active=1`.
* If for every active habit there exists a habit_log on D with `status in ('min','normal')`, then D is Perfect Day.

### 4.2 Streak

* streak(today) = number of consecutive Perfect Days ending at today, going backwards day-by-day.

### 4.3 XP

**Effort XP (by habit group)**

* For each habit_log on date D:

  * status=min → +habit.min_xp
  * status=normal → +habit.normal_xp
* Show by group + total.

**Skill XP (by line)**

* When a quest completion is saved:

  * skill_xp = base * difficulty
  * base default = 10
* Show by line + total.

### 4.4 Evidence mandatory for quest completion

* A quest completion must require evidence_text + evidence_ref (non-empty).
* If missing, block saving.

### 4.5 Quest completion definition

* A quest is considered “completed” if there exists at least one quest_completion record for that quest.
* (V1) allow multiple completions; progress uses existence check.

---

## 5) SQLite Data Model (V1)

### habits

* id (pk)
* name (text)  // user-editable display name
* group (text: growth/health/maintenance)
* min_desc (text)
* normal_desc (text)
* min_xp (int default 1)
* normal_xp (int default 2)
* active (int default 1)
* sort_order (int default 0)
* created_at (text ISO)

### habit_logs (daily status per habit)

* id (pk)
* date (text YYYY-MM-DD)
* habit_id (fk)
* status (text: none/min/normal)
* minutes (int nullable)
* note (text nullable)
* created_at
  Constraint: UNIQUE(date, habit_id)

### lines

* id (pk)
* name (text) // user-editable display name
* type (text: main/side)
* ultimate_goal (text)
* active (int default 1)
* sort_order (int default 0)
* created_at

### quests

* id (pk)
* line_id (fk)
* chapter (text nullable)
* order_idx (int)
* title (text)  // user-editable display name
* dod (text)
* difficulty (int 1-5)
* is_boss (int default 0)
* active (int default 1)
* created_at

### quest_completions

* id (pk)
* date (text YYYY-MM-DD)
* quest_id (fk)
* minutes (int)
* evidence_type (text nullable)
* evidence_text (text)
* evidence_ref (text)
* created_at

### reviews_weekly

* id (pk)
* week_start (text YYYY-MM-DD) UNIQUE
* effective (text)
* friction (text)
* next_change (text)
* created_at

### ui_labels

* key (text pk)
* value (text not null)

### settings (optional)

* key (text pk)
* value (text)

---

## 6) UI Interaction Requirements

### 6.1 Today

* Date picker (default today)
* Habits grouped display; each habit row has 3-state selector
* Saving a habit status writes/upserts habit_logs(date, habit_id)
* Perfect Day indicator updates live
* Show streak value live
* Mainline Focus:

  * dropdown of active lines
  * show Next Action quest title + DoD snippet
  * push buttons:

    * start_25 / start_5 set a default minutes value in a small “completion form”
* Evidence form appears for quest completion:

  * minutes (prefilled 25 or 5)
  * evidence_type (optional)
  * evidence_text (required)
  * evidence_ref (required)
  * Save button blocks if missing required fields
* Feedback card:

  * Effort XP by group + total for selected date
  * Skill XP by line + total for selected date
  * Focus line progress bar

### 6.2 Consistency

* Table/list of habits with edit & active toggle
* Form for add/edit includes group, min_desc, normal_desc, xp fields, sort_order

### 6.3 Mainlines

* Filter toggle: main/side/all
* Lines list; selecting a line shows:

  * ultimate_goal
  * quests list ordered by order_idx
  * quest add/edit form with DoD, difficulty, is_boss
  * progress bar based on completions existence

### 6.4 Reviews

* Week_start selector (default Monday of current week)
* 3 text areas + save (upsert by week_start)

### 6.5 Dashboard

* Show DB summary metrics + current streak
* Include a simple “UI Labels Editor” panel (or link/button to open it)

---

## 7) Implementation Task Breakdown (Codex TODO)

1. Repo structure:

   * `src/fate_core/` (db, crud, rules, labels)
   * `src/fate_app/` (streamlit UI + router)
   * `data/` for sqlite db (gitignored)
2. DB init:

   * init_db() create tables if not exist
3. Core functions:

   * L(key, default)
   * upsert_ui_label(key, value)
   * upsert_habit_log(date, habit_id, status, minutes, note)
   * compute_perfect_day(date)
   * compute_streak(today)
   * compute_effort_xp(date, by_group)
   * compute_skill_xp(date, by_line)
   * get_next_quest(line_id)
   * line_progress(line_id)
4. CRUD:

   * habits CRUD
   * lines CRUD
   * quests CRUD
   * create quest completion with evidence required
   * weekly review upsert
5. Streamlit App:

   * single entry app.py
   * custom sidebar router using label keys for nav texts
6. README + manual acceptance checklist

---

## 8) Acceptance Criteria (V1 Done)

* App launches locally, uses its own DB file under data/
* User can rename habits/lines/quests at any time; history and stats remain correct
* User can edit UI labels (Perfect Day wording, nav titles, button text); app still functions
* Today supports full loop: habit statuses → perfect day → streak → mainline push → evidence → feedback
* Consistency supports habit CRUD and active toggle; inactive habits do not affect perfect day
* Mainlines supports line+quest CRUD and shows progress
* Reviews saves weekly review record
* Dashboard shows summary + label editor

---

## 9) Repo advice (do not break legacy)

* Keep existing `src/gml/` CLI code untouched (legacy).
* Add new packages `fate_core` and `fate_app` in parallel.
* Use a new DB file name, e.g. `data/fate_v1.db`.
