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
        c.execute("SELECT id, task_name, reminder FROM tasks WHERE user_id = ? ORDER BY id", (user_id,))
        return c.fetchall()


def get_task_id_by_index(user_id, index):
    """Return the DB id for the user's task at 1-based index, or None if not found.

    The ordering matches get_tasks (ORDER BY id).
    """
    if index < 1:
        return None
    with connect() as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM tasks WHERE user_id = ? ORDER BY id LIMIT 1 OFFSET ?", (user_id, index - 1))
        row = c.fetchone()
        return row[0] if row else None

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

def update_task(task_id, user_id, new_name=None, new_reminder=None):
    """Update task name and/or reminder for a user's task. Returns True if a row was updated."""
    if new_name is None and new_reminder is None:
        return False
    with connect() as conn:
        c = conn.cursor()
        # Build dynamic query depending on which fields are provided
        fields = []
        params = []
        if new_name is not None:
            fields.append("task_name = ?")
            params.append(new_name)
        if new_reminder is not None:
            fields.append("reminder = ?")
            params.append(new_reminder)
        params.extend([task_id, user_id])
        query = f"UPDATE tasks SET {', '.join(fields)} WHERE id = ? AND user_id = ?"
        c.execute(query, params)
        conn.commit()
        return c.rowcount > 0
