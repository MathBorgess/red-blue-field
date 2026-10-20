from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class Store:
    def __init__(self, root: Path):
        self.root = root
        self.path = root / "control.sqlite3"
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS reviews(id TEXT PRIMARY KEY, run_id TEXT NOT NULL,
                    status TEXT NOT NULL, operation_hash TEXT NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS findings(id TEXT PRIMARY KEY, run_id TEXT NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS assessments(id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS campaigns(id TEXT PRIMARY KEY, body TEXT NOT NULL);
            """)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def put(self, table: str, key: str, body: dict) -> None:
        assert table in {"runs", "campaigns"}
        with self.connect() as db:
            db.execute(f"INSERT OR REPLACE INTO {table}(id,body) VALUES (?,?)", (key, json.dumps(body)))

    def get(self, table: str, key: str) -> dict | None:
        assert table in {"runs", "campaigns", "findings"}
        with self.connect() as db:
            row = db.execute(f"SELECT body FROM {table} WHERE id=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def list(self, table: str, run_id: str | None = None) -> list[dict]:
        assert table in {"runs", "reviews", "findings", "assessments", "campaigns"}
        with self.connect() as db:
            rows = db.execute(f"SELECT body FROM {table}" + (" WHERE run_id=?" if run_id else "") + " ORDER BY rowid DESC",
                              (run_id,) if run_id else ()).fetchall()
        return [json.loads(r[0]) for r in rows]

    def recover(self) -> list[dict]:
        interrupted = []
        for run in self.list("runs"):
            if run["status"] not in {"complete", "interrupted", "invalid"}:
                run.update(status="interrupted", error="Process restarted; effects require reconciliation")
                self.put("runs", run["id"], run)
                interrupted.append(run)
        for campaign in self.list('campaigns'):
            if campaign['status'] in {'scheduled', 'running'}:
                campaign.update(status='interrupted', error='Process restarted; campaign was not resumed')
                self.put('campaigns', campaign['id'], campaign)
        return interrupted
