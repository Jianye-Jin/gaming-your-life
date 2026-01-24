# ARCHITECTURE

## Repo structure (current)
- `pyproject.toml`: packaging + console script entrypoint `fate`
- `src/gml/cli.py`: CLI entry; parses args; interactive logging; pass gate; chest update; subcommands
- `src/gml/db.py`: SQLite schema + CRUD (tasks, logs, chests) + backup helper
- `src/gml/export_xlsx.py`: export DB -> XLSX (TASKS/LOG/CHESTS)
- `src/gml/export_csv.py`: export DB -> CSV bundle (tasks.csv/log.csv/chests.csv)
- `src/gml/cli_xlsx_legacy.py`: legacy Excel-based CLI (kept only for reference)
- `v0.1/`: legacy scripts and old XLSX approach (not used in production path)

## Data model (SQLite)
- `tasks(id, name, domain, cadence, default_minutes, default_xp, active, created_at)`
- `logs(id, ts, date, task_id, minutes, xp, notes)` (facts; append-only)
- `chests(date, eligible, revealed, revealed_ts)`

## Data flow
1. User runs `fate` (or `fate --date ...` / `fate --reveal`)
2. `cli.py` lists active tasks from DB
3. User selects Task_IDs; inputs minutes + notes
4. `db.insert_log()` appends rows into `logs`
5. `db.counts_for_date()` computes per-domain counts + totals
6. Daily Pass computed in CLI (BODY>=1 & MAIN>=1 & HOME>=1)
7. If pass: `db.mark_chest(date, reveal=--reveal)`
8. Export commands read DB and write files under `~/.fate/exports/`

## Privacy boundaries
- Repo must not contain any `.db/.sqlite3/.xlsx/.csv` personal data
- `.gitignore` must ignore `*.db *.sqlite3 *.xlsx *.csv` and build artifacts (e.g., `*.egg-info/`)
