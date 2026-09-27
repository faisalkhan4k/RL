"""SQLite checkpoint boundary: whole completed turns commit atomically."""
import json
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as db:
            db.executescript('''
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, state TEXT NOT NULL, updated REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS feedback(session_id TEXT, turn_id TEXT, helpful INTEGER,
                    PRIMARY KEY(session_id, turn_id), FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.execute('PRAGMA foreign_keys=ON')
        try:
            with db:
                yield db
        finally:
            db.close()

    def create(self):
        sid = secrets.token_urlsafe(32)
        self.save(sid, {'messages': [], 'requirements': {}, 'cart': [], 'turn_ids': [], 'events': []})
        return sid

    def get(self, sid):
        with self.connect() as db:
            db.execute('DELETE FROM sessions WHERE updated < ?', (time.time() - 86400,))
            row = db.execute('SELECT state FROM sessions WHERE id=?', (sid,)).fetchone()
        return json.loads(row[0]) if row else None

    def save(self, sid, state):
        with self.connect() as db:
            db.execute('INSERT INTO sessions VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET state=excluded.state, updated=excluded.updated',
                       (sid, json.dumps(state), time.time()))

    def delete(self, sid):
        with self.connect() as db:
            db.execute('DELETE FROM sessions WHERE id=?', (sid,))

    def rate(self, sid, turn_id, helpful):
        with self.connect() as db:
            cur = db.execute('INSERT OR IGNORE INTO feedback VALUES(?,?,?)', (sid, turn_id, int(helpful)))
            return cur.rowcount == 1
