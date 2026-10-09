import hashlib
import json
import sqlite3
from pathlib import Path


def case_hash(problem: str, code: str) -> str:
    return hashlib.sha256((problem.strip() + "\n#\n" + code.strip()).encode()).hexdigest()


class Store:
    def __init__(self, db_path: str):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(db_path)
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS analyses (
                hash TEXT PRIMARY KEY,
                ts TEXT DEFAULT CURRENT_TIMESTAMP,
                title TEXT,
                category TEXT,
                result TEXT)"""
        )

    def get(self, h: str):
        row = self.db.execute("SELECT result FROM analyses WHERE hash=?", (h,)).fetchone()
        return json.loads(row[0]) if row else None

    def save(self, h: str, title: str, data: dict):
        self.db.execute(
            "INSERT OR REPLACE INTO analyses (hash, title, category, result) VALUES (?,?,?,?)",
            (h, title, data["bug_category"], json.dumps(data)),
        )
        self.db.commit()

    def category_counts(self):
        return self.db.execute(
            "SELECT category, COUNT(*) c FROM analyses GROUP BY category ORDER BY c DESC"
        ).fetchall()
