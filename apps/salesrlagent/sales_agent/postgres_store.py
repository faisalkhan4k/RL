"""PostgreSQL deployment store with the same session boundary as local SQLite."""
import json
import secrets
import time
from contextlib import contextmanager

class PostgresStore:
    def __init__(self,url):
        import psycopg
        self.url=url;self.driver=psycopg
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, state TEXT NOT NULL, updated DOUBLE PRECISION NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS feedback(session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE, turn_id TEXT, helpful INTEGER, PRIMARY KEY(session_id,turn_id))')
    @contextmanager
    def connect(self):
        with self.driver.connect(self.url,connect_timeout=5) as db:yield db
    def create(self):
        sid=secrets.token_urlsafe(32)
        self.save(sid,{'messages':[],'requirements':{},'cart':[],'turn_ids':[],'events':[]})
        return sid
    def get(self,sid):
        with self.connect() as db:
            db.execute('DELETE FROM sessions WHERE updated < %s',(time.time()-86400,))
            row=db.execute('SELECT state FROM sessions WHERE id=%s',(sid,)).fetchone()
        return json.loads(row[0]) if row else None
    def save(self,sid,state):
        with self.connect() as db:
            db.execute('INSERT INTO sessions VALUES(%s,%s,%s) ON CONFLICT(id) DO UPDATE SET state=EXCLUDED.state, updated=EXCLUDED.updated',(sid,json.dumps(state),time.time()))
    def delete(self,sid):
        with self.connect() as db:db.execute('DELETE FROM sessions WHERE id=%s',(sid,))
    def rate(self,sid,turn_id,helpful):
        with self.connect() as db:
            return db.execute('INSERT INTO feedback VALUES(%s,%s,%s) ON CONFLICT DO NOTHING',(sid,turn_id,int(helpful))).rowcount==1
