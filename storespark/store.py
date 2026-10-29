"""使用 SQLite 保存任务、对话、素材和内容，保留失败前已有输入。"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, data_dir: Path):
        data_dir.mkdir(parents=True, exist_ok=True)
        self.path = data_dir / "storespark.sqlite3"
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, brief TEXT NOT NULL,
                    channel TEXT NOT NULL, format TEXT NOT NULL, status TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id),
                    role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS materials (
                    id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id),
                    name TEXT NOT NULL, media_type TEXT NOT NULL, size INTEGER NOT NULL,
                    content BLOB NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id),
                    kind TEXT NOT NULL, title TEXT NOT NULL, content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS messages_task ON messages(task_id);
                CREATE INDEX IF NOT EXISTS materials_task ON materials(task_id);
                CREATE INDEX IF NOT EXISTS artifacts_task ON artifacts(task_id);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def get_setting(self, name: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT value FROM settings WHERE name=?", (name,)).fetchone()
            return json.loads(row["value"]) if row else None

    def set_setting(self, name: str, value: dict) -> None:
        with self.connect() as db:
            db.execute("INSERT INTO settings(name,value) VALUES(?,?) ON CONFLICT(name) DO UPDATE SET value=excluded.value",
                       (name, json.dumps(value, ensure_ascii=False)))

    def list_tasks(self) -> list[dict]:
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM tasks ORDER BY updated_at DESC, rowid DESC")]

    def create_task(self, payload: dict) -> dict:
        stamp = now()
        task = {"id": uuid4().hex, **payload, "status": "draft", "created_at": stamp, "updated_at": stamp}
        with self.connect() as db:
            db.execute("INSERT INTO tasks VALUES(:id,:title,:brief,:channel,:format,:status,:created_at,:updated_at)", task)
        return task

    def get_task(self, task_id: str) -> dict | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            if not row:
                return None
            result = dict(row)
            for table in ("messages", "artifacts"):
                result[table] = [dict(item) for item in db.execute(
                    f"SELECT * FROM {table} WHERE task_id=? ORDER BY rowid", (task_id,))]
            result["materials"] = [dict(item) for item in db.execute(
                "SELECT id,name,media_type,size,created_at FROM materials WHERE task_id=? ORDER BY rowid", (task_id,))]
            return result

    def add_message(self, task_id: str, role: str, content: str) -> dict:
        message = {"id": uuid4().hex, "task_id": task_id, "role": role, "content": content, "created_at": now()}
        with self.connect() as db:
            db.execute("INSERT INTO messages VALUES(:id,:task_id,:role,:content,:created_at)", message)
            db.execute("UPDATE tasks SET updated_at=? WHERE id=?", (message["created_at"], task_id))
        return message

    def complete_turn(self, task_id: str, reply: str, status: str, artifact: dict | None) -> None:
        stamp = now()
        with self.connect() as db:
            db.execute("INSERT INTO messages VALUES(?,?,?,?,?)", (uuid4().hex, task_id, "assistant", reply, stamp))
            if artifact:
                db.execute("INSERT INTO artifacts VALUES(?,?,?,?,?,?)", (
                    uuid4().hex, task_id, "copy", artifact["title"], artifact["content"], stamp))
            db.execute("UPDATE tasks SET status=?,updated_at=? WHERE id=?", (status, stamp, task_id))

    def add_material(self, task_id: str, name: str, media_type: str, content: bytes) -> dict:
        stamp = now()
        material = {"id": uuid4().hex, "name": name, "media_type": media_type, "size": len(content), "created_at": stamp}
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            count, total = db.execute("SELECT COUNT(*),COALESCE(SUM(size),0) FROM materials WHERE task_id=?", (task_id,)).fetchone()
            if count >= 6 or total + len(content) > 20 * 1024 * 1024:
                raise ValueError("每个任务最多 6 份素材，总大小不超过 20 MB")
            db.execute("INSERT INTO materials VALUES(?,?,?,?,?,?,?)", (
                material["id"], task_id, name, media_type, len(content), content, stamp))
            db.execute("UPDATE tasks SET updated_at=? WHERE id=?", (stamp, task_id))
        return material

    def material_content(self, task_id: str) -> list[dict]:
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM materials WHERE task_id=? ORDER BY rowid", (task_id,))]

    def edit_artifact(self, task_id: str, artifact_id: str, title: str, content: str) -> dict | None:
        with self.connect() as db:
            if not db.execute("SELECT 1 FROM artifacts WHERE id=? AND task_id=?", (artifact_id, task_id)).fetchone():
                return None
            db.execute("UPDATE artifacts SET title=?,content=? WHERE id=? AND task_id=?", (title, content, artifact_id, task_id))
            db.execute("UPDATE tasks SET updated_at=? WHERE id=?", (now(), task_id))
            return dict(db.execute("SELECT * FROM artifacts WHERE id=?", (artifact_id,)).fetchone())
