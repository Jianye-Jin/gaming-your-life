# Gaming My Life (GML)

A local-first, gamified personal growth tracker.
- Code is public.
- Personal data (xlsx/csv/sqlite) stays local and is ignored by git.

## Run (v0.1)
- See `v0.1/` folder.

## Fate V1 (Streamlit + SQLite)
Install deps and run:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
streamlit run src/fate_app/app.py
```

The app stores data in `data/fate_v1.db` (gitignored).

## Fate V1 Acceptance Checklist
- Today page: habits logged, Perfect Day + streak update, mainline push saves evidence.
- Consistency page: create/edit/disable habits, groups and XP update.
- Mainlines page: create/edit lines and quests, progress shows.
- Reviews page: weekly review saves by week_start.
- Dashboard: streak + totals + label editor works, label edits update UI immediately.
