# TASKS (next steps)

## P0 — Must have (stability + daily use)
1) Add `fate stats` (today / week)
- Output: daily counts, total minutes, total xp, daily pass, streak
- Acceptance: `fate stats today` and `fate stats week` run without errors, matches DB facts.

2) Make XP rules configurable (no historical loss)
- Store raw facts in `logs` (already).
- Add a rule function to compute XP (e.g., minutes-based or per-task).
- Acceptance: changing rule recomputes XP for a date range without modifying raw logs.

## P1 — Quality (agent-friendly + maintainable)
3) Add minimal tests
- Unit test for daily pass rule and counts_for_date
- Acceptance: `python -m pytest` passes.

4) Improve README quickstart
- Include: install, init DB, add tasks, log day, export, privacy note
- Acceptance: a fresh user can run from clone to first log in < 5 minutes.

## P2 — Nice to have
5) `fate export json` (for dashboards)
- Acceptance: JSON schema documented + export works for date ranges.

6) Replace interactive input with optional non-interactive flags
- Example: `fate log --id B001 --minutes 20 --notes "..."`
- Acceptance: can log without prompts.

