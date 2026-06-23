"""
Admin utility: completely resets the database (deletes all data!) and
re-initializes it with a fresh schema and seed data (roles + predefined
departments). Use this only when you want to start over — for example,
when setting up a demo, or wiping test data before going live.

Usage:
    python reset_database.py

You will be asked to type 'RESET' to confirm, since this is destructive
and cannot be undone.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database.db import init_database, DB_PATH
from app.database.seed import run_seed


def main():
    print("=" * 60)
    print("  DatAInspire Task Command Center — Database Reset")
    print("=" * 60)
    print(f"\nThis will permanently DELETE the database at:\n  {DB_PATH}\n")
    print("All users, tasks, comments, and files records will be lost.")
    print("(Uploaded files on disk are not deleted by this script.)\n")

    confirm = input("Type RESET to confirm, or anything else to cancel: ").strip()
    if confirm != "RESET":
        print("Cancelled. No changes made.")
        return

    init_database(force=True)
    run_seed()
    print("\n✅ Database has been reset and re-seeded with default roles and departments.")
    print("   Run the app again and you'll be prompted to create the first President account.")


if __name__ == "__main__":
    main()
