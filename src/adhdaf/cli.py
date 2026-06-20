import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path


def backup(db_path: str = "data/adhdaf.db", backup_dir: str = "data/backups"):
    db = Path(db_path)
    if not db.exists():
        print(f"Database not found: {db}")
        sys.exit(1)

    dest_dir = Path(backup_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    dest = dest_dir / f"adhdaf-{timestamp}.db"
    shutil.copy2(db, dest)
    print(f"Backed up to {dest}")

    backups = sorted(dest_dir.glob("adhdaf-*.db"))
    while len(backups) > 30:
        oldest = backups.pop(0)
        oldest.unlink()
        print(f"Removed old backup: {oldest}")


def main():
    parser = argparse.ArgumentParser(prog="adhdaf")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("backup", help="Back up the database")
    args = parser.parse_args()

    if args.command == "backup":
        backup()
    else:
        parser.print_help()
