from peewee import SqliteDatabase
import os
from pathlib import Path

# Create a dedicated directory in the user's home folder for the app's data
app_dir = Path.home() / '.workitems'
app_dir.mkdir(parents=True, exist_ok=True)
db_path = app_dir / 'workitems.db'

# Configure a SqliteDatabase with WAL mode and busy_timeout=5000 as requested
db = SqliteDatabase(
    db_path,
    pragmas={
        'journal_mode': 'wal',
        'busy_timeout': 5000,
        'cache_size': -1024 * 64,  # 64MB cache
        'foreign_keys': 1,
        'synchronous': 1
    }
)
