# Repository Guidelines

## Project Structure & Module Organization
- `src/gml/` holds the current Python package (CLI, exports, and SQLite logic).
- `src/fate_gml.egg-info/` is build metadata; do not edit by hand.
- `v0.1/` contains legacy scripts and the original XLSX workflow (kept for reference).
- Root docs like `README.md`, `ARCHITECTURE.md`, and `TASKS.md` capture product intent.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` creates an isolated env.
- `pip install -e .` installs the CLI in editable mode; exposes the `fate` command.
- `python -m gml.cli` runs the CLI directly from source.
- `pip install -r requirements-dev.txt` installs dev tools (pytest, ruff).
- Legacy: `python v0.1/gml_cli.py` runs the v0.1 CLI.

## Coding Style & Naming Conventions
- Python 3.11+, 4-space indentation, PEP 8 conventions.
- Use `snake_case` for functions/variables, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants.
- Lint/format with Ruff: `ruff check src` and `ruff format src`.

## Testing Guidelines
- Test framework: pytest (see `requirements-dev.txt`).
- No test suite is present yet; add tests under `tests/` with `test_*.py` naming.
- Run tests with `pytest` from the repo root.

## Commit & Pull Request Guidelines
- Commit messages follow a Conventional Commits style (`feat:`, `docs:`, `chore:`, `init:`).
- Keep commits focused; avoid mixing refactors with behavior changes.
- PRs should include a clear summary, linked issue (if any), and note any data/schema changes.

## Data & Local Configuration
- Personal data (xlsx/csv/sqlite) should remain local and untracked.
- If you add new data outputs, update `.gitignore` to keep them out of version control.

# Codex instructions for this repo
- Read and follow PRD in: PRD_V1.md
- Do NOT modify legacy code under: src/gml/** and v0.1/**
- Implement new app in:
  - src/fate_core/**
  - src/fate_app/**
- Use SQLite DB at: data/fate_v1.db (gitignored)
- Use stable IDs for logic; all UI labels must be editable via ui_labels table per PRD.
- Make small commits with clear messages.
- After changes, provide:
  - how to run the app
  - how to run minimal sanity checks

## Logging (MANDATORY)
- Maintain a repo log in docs/codex/ (daily file: docs/codex/YYYY-MM-DD.md).
- For every user request:
  1) First append the user prompt verbatim to today's log.
  2) After finishing, append: plan summary, commands run, files changed, and commit SHA(s).
- Never skip logging even for small edits.
