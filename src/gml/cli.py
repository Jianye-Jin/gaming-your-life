#!/usr/bin/env python3
"""
Fate (Gaming My Life) — SQLite edition

Behavior aligned with your current Excel CLI:
- Interactive: input Task_IDs -> minutes -> notes
- Daily pass gate: BODY>=1 and MAIN>=1 and HOME>=1
- If pass: mark chest eligible; with --reveal also mark revealed
- Subcommand: fate init (safe, idempotent; won't overwrite unless --force)

Data lives locally:
- default DB: ~/.fate/fate.db
- env override: FATE_DB=/path/to/fate.db
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from pathlib import Path

from gml import db
from gml.export_xlsx import export_xlsx
from gml.export_csv import export_csv_bundle

def today_str() -> str:
    return dt.date.today().isoformat()


def default_db_path_str() -> str:
    p = os.environ.get("FATE_DB")
    if p:
        return str(Path(p).expanduser())
    return str(Path("~/.fate/fate.db").expanduser())


def cmd_init(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="fate init", description="Initialize a local SQLite DB for Fate.")
    ap.add_argument("--db", type=str, default=default_db_path_str(), help="DB path (default: ~/.fate/fate.db)")
    ap.add_argument("--seed", action="store_true", help="Seed a few starter tasks if tasks table is empty.")
    ap.add_argument("--force", action="store_true", help="DANGEROUS: overwrite existing DB (will backup first).")
    args = ap.parse_args(argv)

    db_path = Path(args.db).expanduser().resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if db_path.exists() and args.force:
        # backup then overwrite
        db.backup_before_write(db_path)
        db_path.unlink()

    # idempotent init (safe if exists)
    db.init_db(db_path)

    if args.seed:
        db.seed_tasks_if_empty(db_path)

    print(f"✅ DB ready: {db_path}")
    if args.seed:
        print("✅ Seeded starter tasks.")
    print("Tip: set env var FATE_DB to pin the DB path.")


def cmd_task_list(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="fate task list")
    ap.add_argument("--db", type=str, default=default_db_path_str())
    args = ap.parse_args(argv)

    db_path = Path(args.db).expanduser().resolve()
    db.init_db(db_path)

    tasks = db.list_tasks(db_path)
    if not tasks:
        print("No tasks found.")
        print("Run: fate init --seed   OR   fate task add ...")
        return

    for t in tasks:
        print(f"  {t['id']:6s} [{t['domain']}] {t['name']} (default {t['default_minutes']} min)")


def cmd_task_add(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="fate task add")
    ap.add_argument("--db", type=str, default=default_db_path_str())
    ap.add_argument("--id", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--domain", required=True, choices=["BODY", "MAIN", "HOME", "EXP"])
    ap.add_argument("--cadence", default="daily")
    ap.add_argument("--default-minutes", type=int, default=0)
    ap.add_argument("--default-xp", type=int, default=0)
    args = ap.parse_args(argv)

    db_path = Path(args.db).expanduser().resolve()
    db.init_db(db_path)

    db.add_task(
        db_path,
        tid=args.id.strip().upper(),
        name=args.name.strip(),
        domain=args.domain.strip().upper(),
        cadence=args.cadence.strip(),
        default_minutes=args.default_minutes,
        default_xp=args.default_xp,
    )
    print(f"✅ Added task: {args.id.strip().upper()} [{args.domain.strip().upper()}] {args.name.strip()}")

def cmd_export_xlsx(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="fate export xlsx", description="Export SQLite data to an XLSX workbook.")
    ap.add_argument("--db", type=str, default=default_db_path_str())
    ap.add_argument("--out", type=str, default=None, help="Output .xlsx path (default: ~/.fate/exports/...)")
    ap.add_argument("--since", type=str, default=None, help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--until", type=str, default=None, help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite if output exists.")
    args = ap.parse_args(argv)

    db_path = Path(args.db).expanduser().resolve()

    if args.out:
        out_path = Path(args.out).expanduser().resolve()
    else:
        export_dir = Path("~/.fate/exports").expanduser()
        ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = export_dir / f"fate_export_{ts}.xlsx"

    if out_path.exists() and not args.overwrite:
        raise SystemExit(f"Output exists: {out_path}\nUse --overwrite or provide a new --out path.")

    out = export_xlsx(db_path=db_path, out_path=out_path, since=args.since, until=args.until)
    print(f"✅ Exported: {out}")

def cmd_export_csv(argv: list[str]) -> None:
    ap = argparse.ArgumentParser(prog="fate export csv", description="Export SQLite data to CSV files.")
    ap.add_argument("--db", type=str, default=default_db_path_str())
    ap.add_argument("--out-dir", type=str, default=None, help="Output directory (default: ~/.fate/exports/csv/<timestamp>/)")
    ap.add_argument("--since", type=str, default=None, help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--until", type=str, default=None, help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite output files if they exist.")
    args = ap.parse_args(argv)

    db_path = Path(args.db).expanduser().resolve()

    if args.out_dir:
        out_dir = Path(args.out_dir).expanduser().resolve()
    else:
        base = Path("~/.fate/exports/csv").expanduser()
        ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = base / ts

    out = export_csv_bundle(
        db_path=db_path,
        out_dir=out_dir,
        since=args.since,
        until=args.until,
        overwrite=args.overwrite,
    )
    print(f"✅ Exported CSV folder: {out}")
    print(f"   - {out / 'tasks.csv'}")
    print(f"   - {out / 'log.csv'}")
    print(f"   - {out / 'chests.csv'}")

def interactive_daily(db_path: Path, date_str: str, reveal: bool) -> None:
    tasks = db.list_tasks(db_path)
    if not tasks:
        print("No tasks found.")
        print("Run: fate init --seed   OR   fate task add ...")
        return

    print(f"\nFate — {date_str}\n")
    print("Pick tasks you completed today (comma separated Task_ID), or press Enter to skip logging.\n")
    print("Available tasks:")
    for t in tasks:
        print(f"  {t['id']:6s} [{t['domain']}] {t['name']}")

    raw = input("\nTask_IDs: ").strip()
    if raw:
        ids = [x.strip().upper() for x in raw.split(",") if x.strip()]
        task_map = {str(t["id"]): t for t in tasks}

        # Safety: backup DB before we write
        db.backup_before_write(db_path)

        for tid in ids:
            match = task_map.get(tid)
            if not match:
                print(f"  ! Unknown Task_ID: {tid} (skipped)")
                continue

            default_m = int(match["default_minutes"] or 0)
            mins_raw = input(f"  Minutes for {tid} (default {default_m}): ").strip()
            minutes = int(mins_raw) if mins_raw else default_m
            notes = input("  Notes (optional): ").strip()

            db.insert_log(db_path, date_str, tid, minutes, notes)
            print("  ✓ logged")

    counts, total_minutes, total_xp = db.counts_for_date(db_path, date_str)
    daily_pass = (counts["BODY"] >= 1 and counts["MAIN"] >= 1 and counts["HOME"] >= 1)

    print("\nToday summary:")
    print(f"  BODY={counts['BODY']}  MAIN={counts['MAIN']}  HOME={counts['HOME']}  EXP={counts['EXP']}  minutes={total_minutes}  xp={total_xp}")
    print(f"  Daily Pass: {'YES' if daily_pass else 'NO'} (needs BODY>=1 & MAIN>=1 & HOME>=1)")

    if daily_pass:
        db.mark_chest(db_path, date_str, reveal=reveal)
        print("  Chest: eligible marked" + (" + revealed" if reveal else ""))

    print(f"\nDB: {db_path}\n")


def main():
    # subcommands
    if len(sys.argv) >= 2 and sys.argv[1] == "init":
        cmd_init(sys.argv[2:])
        return
    if len(sys.argv) >= 3 and sys.argv[1] == "task" and sys.argv[2] == "list":
        cmd_task_list(sys.argv[3:])
        return
    if len(sys.argv) >= 3 and sys.argv[1] == "task" and sys.argv[2] == "add":
        cmd_task_add(sys.argv[3:])
        return
    if len(sys.argv) >= 3 and sys.argv[1] == "export" and sys.argv[2] == "xlsx":
        cmd_export_xlsx(sys.argv[3:])
        return
    if len(sys.argv) >= 3 and sys.argv[1] == "export" and sys.argv[2] == "csv":
        cmd_export_csv(sys.argv[3:])
        return

    # default command (aligned with your current interface)
    ap = argparse.ArgumentParser()
    # keep a compatibility alias: --file works as --db (so your muscle memory won't break)
    ap.add_argument("--db", type=str, default=default_db_path_str())
    ap.add_argument("--file", type=str, default=None, help="(deprecated) alias of --db")
    ap.add_argument("--date", type=str, default=today_str())
    ap.add_argument("--reveal", action="store_true", help="also reveal (open) today's chest if Daily Pass")
    args = ap.parse_args()

    db_path = Path((args.file or args.db)).expanduser().resolve()
    db.init_db(db_path)

    interactive_daily(db_path, args.date, reveal=args.reveal)


if __name__ == "__main__":
    main()
