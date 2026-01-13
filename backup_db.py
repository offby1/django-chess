#!/usr/bin/env python3
"""Safely backup SQLite database using VACUUM INTO."""

import sqlite3
import sys

def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else '/chess/data/db.sqlite3'
    backup_path = sys.argv[2] if len(sys.argv) > 2 else '/chess/data/backup.db'

    conn = sqlite3.connect(db_path)
    conn.execute(f"VACUUM INTO '{backup_path}'")
    conn.close()
    print(f'Backup created successfully: {backup_path}')

if __name__ == '__main__':
    main()
