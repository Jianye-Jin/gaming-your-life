# PROJECT_BRIEF

## One-line goal
Build a local-first CLI game system ("Fate") to log daily actions and compute daily pass + rewards, with reliable storage and easy exports for visualization.

## Core features
- CLI command: `fate`
- Interactive logging: choose task IDs -> minutes -> notes
- Daily Pass rule: BODY>=1 AND MAIN>=1 AND HOME>=1
- Chest system: if pass -> mark eligible; `--reveal` also marks revealed
- Task management: `fate task list`, `fate task add ...`
- Storage: SQLite (single source of truth)
- Export: `fate export xlsx`, `fate export csv`

## Constraints / non-goals
- Local-first: personal data must NEVER be committed to git
- Public repo OK: only code/docs in GitHub; data in `~/.fate/`
- Default runtime data paths:
  - DB: `~/.fate/fate.db` (override via `FATE_DB`)
  - Backups: `~/.fate/backups/`
  - Exports: `~/.fate/exports/`
- Python >= 3.11, dependency: openpyxl (for XLSX export)
- No cloud, no web service deployment (CLI-only)
