import sqlite3
from datetime import datetime

DB_NAME = "tasks.db"

def connect():
    return sqlite3.connect(DB_NAME)

def create_table():
    with connect() as conn:
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            task_name TEXT NOT NULL,
            reminder TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)
        conn.commit()

def add_task(user_id, task_name, reminder):
    with connect() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO tasks (user_id, task_name, reminder, created_at) VALUES (?, ?, ?, ?)",
                  (user_id, task_name, reminder, datetime.utcnow().isoformat()))
        conn.commit()

def get_tasks(user_id):
    with connect() as conn:
        c = conn.cursor()
        c.execute("SELECT id, task_name, reminder FROM tasks WHERE user_id = ?", (user_id,))
        return c.fetchall()

def remove_task(task_id, user_id):
    with connect() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        conn.commit()

def clear_tasks(user_id):
    with connect() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE user_id = ?", (user_id,))
        conn.commit()
