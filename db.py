"""SQLite layer. Thin wrapper, no ORM."""
import sqlite3
from datetime import date, datetime
from pathlib import Path
from config import DB_PATH


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            total_hours REAL NOT NULL,
            hours_logged REAL NOT NULL DEFAULT 0,
            deadline TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',  -- active | completed | failed
            created_at TEXT NOT NULL,
            closed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            hours REAL NOT NULL,       -- positive for +, negative for correction
            logged_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS growth (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            percent REAL NOT NULL DEFAULT 0,
            cycle_start TEXT NOT NULL  -- ISO date of last May 28 reset
        );

        CREATE TABLE IF NOT EXISTS emotional_clicks (
            click_date TEXT PRIMARY KEY  -- YYYY-MM-DD
        );
        """)

        # Ensure singleton growth row exists
        row = c.execute("SELECT id FROM growth WHERE id = 1").fetchone()
        if not row:
            c.execute(
                "INSERT INTO growth (id, percent, cycle_start) VALUES (1, 0, ?)",
                (date.today().isoformat(),),
            )


# ---------- Projects ----------
def add_project(name: str, total_hours: float, deadline: str) -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO projects (name, total_hours, deadline, created_at) VALUES (?, ?, ?, ?)",
            (name, total_hours, deadline, datetime.now().isoformat()),
        )
        return cur.lastrowid


def get_active_projects():
    with _conn() as c:
        return c.execute(
            "SELECT * FROM projects WHERE status = 'active' ORDER BY deadline ASC"
        ).fetchall()


def get_active_count() -> int:
    with _conn() as c:
        return c.execute(
            "SELECT COUNT(*) FROM projects WHERE status = 'active'"
        ).fetchone()[0]


def update_project_hours(project_id: int, new_hours: float):
    with _conn() as c:
        c.execute(
            "UPDATE projects SET hours_logged = ? WHERE id = ?",
            (new_hours, project_id),
        )


def close_project(project_id: int, status: str):
    """status = 'completed' or 'failed'"""
    with _conn() as c:
        c.execute(
            "UPDATE projects SET status = ?, closed_at = ? WHERE id = ?",
            (status, datetime.now().isoformat(), project_id),
        )


def log_session(project_id: int, hours: float):
    with _conn() as c:
        c.execute(
            "INSERT INTO sessions (project_id, hours, logged_at) VALUES (?, ?, ?)",
            (project_id, hours, datetime.now().isoformat()),
        )


# ---------- Growth ----------
def get_growth():
    with _conn() as c:
        return c.execute("SELECT percent, cycle_start FROM growth WHERE id = 1").fetchone()


def set_growth(percent: float, cycle_start: str = None):
    with _conn() as c:
        if cycle_start:
            c.execute(
                "UPDATE growth SET percent = ?, cycle_start = ? WHERE id = 1",
                (percent, cycle_start),
            )
        else:
            c.execute("UPDATE growth SET percent = ? WHERE id = 1", (percent,))


# ---------- Emotional clicks ----------
def emotional_clicks_today(today_iso: str) -> int:
    with _conn() as c:
        return c.execute(
            "SELECT COUNT(*) FROM emotional_clicks WHERE click_date = ?",
            (today_iso,),
        ).fetchone()[0]


def record_emotional_click(today_iso: str):
    with _conn() as c:
        c.execute("INSERT INTO emotional_clicks (click_date) VALUES (?)", (today_iso,))