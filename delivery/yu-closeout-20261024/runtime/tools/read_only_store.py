"""Small read-only SQLite connection with bounded waits and VM execution."""
from pathlib import Path
import sqlite3
import time


def connect(path,timeout=.75):
    con=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True,timeout=timeout)
    con.row_factory=sqlite3.Row;con.execute('PRAGMA query_only=ON')
    deadline=time.monotonic()+timeout;con.set_progress_handler(lambda:int(time.monotonic()>deadline),1000)
    return con
