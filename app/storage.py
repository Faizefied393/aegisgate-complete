"""Persistent SQLite audit, ticket, and detection records."""
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def connect():
    path = Path(os.environ.get("AEGIS_DB", "data/aegisgate.db"))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=10000")
    db.execute("CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY, ts TEXT, user TEXT, tool TEXT, resource TEXT, decision TEXT, outcome TEXT, trace_id TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY, title TEXT NOT NULL, created_by TEXT NOT NULL, ts TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS findings (id INTEGER PRIMARY KEY, ts TEXT, user TEXT, rule TEXT, detail TEXT)")
    db.commit()
    return db

def audit(user, tool, resource, decision, outcome, trace_id):
    with connect() as db:
        db.execute("INSERT INTO audit (ts,user,tool,resource,decision,outcome,trace_id) VALUES (?,?,?,?,?,?,?)", (utc_now(), user, tool, resource, decision, outcome, trace_id))
        # Deterministic detection: 3+ denials from same user in last 5 minutes.
        if decision == "DENY":
            # ISO timestamps with T compare lexically poorly to SQLite datetime format;
            # use Python cutoff with same ISO representation instead.
            from datetime import timedelta
            cutoff = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
            count = db.execute("SELECT COUNT(*) FROM audit WHERE user=? AND decision='DENY' AND ts>=?", (user, cutoff)).fetchone()[0]
            if count == 3:
                db.execute("INSERT INTO findings (ts,user,rule,detail) VALUES (?,?,?,?)", (utc_now(),user,"repeated_denials","Three denials in five minutes"))
        db.commit()

def rows(table, limit=100):
    if table not in {"audit", "tickets", "findings"}:
        raise ValueError("unsupported table")
    with connect() as db:
        return [dict(r) for r in db.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT ?", (limit,)).fetchall()]
