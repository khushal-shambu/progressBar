"""SQLite layer. Thin wrapper, no ORM."""
import sqlite3
from datetime import date, datetime
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
            status TEXT NOT NULL DEFAULT 'active',  -- active | completed | failed | abandoned
            created_at TEXT NOT NULL,
            closed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            hours REAL NOT NULL,
            logged_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS growth (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            percent REAL NOT NULL DEFAULT 0,
            cycle_start TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS emotional_clicks (
            click_date TEXT PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS timer_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            project_id INTEGER,
            started_at TEXT,
            extended_until_minutes INTEGER DEFAULT 90
        );
        """)

        row = c.execute("SELECT id FROM growth WHERE id = 1").fetchone()
        if not row:
            c.execute(
                "INSERT INTO growth (id, percent, cycle_start) VALUES (1, 0, ?)",
                (date.today().isoformat(),),
            )

        row = c.execute("SELECT id FROM timer_state WHERE id = 1").fetchone()
        if not row:
            c.execute("INSERT INTO timer_state (id, project_id, started_at) VALUES (1, NULL, NULL)")


# ---------- Projects ----------
def add_project(name, total_hours, deadline):
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


def get_active_count():
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM projects WHERE status = 'active'").fetchone()[0]


def update_project_hours(project_id, new_hours):
    with _conn() as c:
        c.execute("UPDATE projects SET hours_logged = ? WHERE id = ?", (new_hours, project_id))


def close_project(project_id, status):
    """status = 'completed' | 'failed' | 'abandoned'"""
    with _conn() as c:
        c.execute(
            "UPDATE projects SET status = ?, closed_at = ? WHERE id = ?",
            (status, datetime.now().isoformat(), project_id),
        )


def log_session(project_id, hours):
    with _conn() as c:
        c.execute(
            "INSERT INTO sessions (project_id, hours, logged_at) VALUES (?, ?, ?)",
            (project_id, hours, datetime.now().isoformat()),
        )


# ---------- Growth ----------
def get_growth():
    with _conn() as c:
        return c.execute("SELECT percent, cycle_start FROM growth WHERE id = 1").fetchone()


def set_growth(percent, cycle_start=None):
    with _conn() as c:
        if cycle_start:
            c.execute("UPDATE growth SET percent = ?, cycle_start = ? WHERE id = 1", (percent, cycle_start))
        else:
            c.execute("UPDATE growth SET percent = ? WHERE id = 1", (percent,))


# ---------- Emotional ----------
def emotional_clicks_today(today_iso):
    with _conn() as c:
        return c.execute(
            "SELECT COUNT(*) FROM emotional_clicks WHERE click_date = ?", (today_iso,)
        ).fetchone()[0]


def record_emotional_click(today_iso):
    with _conn() as c:
        c.execute("INSERT INTO emotional_clicks (click_date) VALUES (?)", (today_iso,))


# ---------- Timer ----------
def get_timer():
    with _conn() as c:
        return c.execute("SELECT project_id, started_at, extended_until_minutes FROM timer_state WHERE id = 1").fetchone()


def start_timer(project_id):
    with _conn() as c:
        c.execute(
            "UPDATE timer_state SET project_id = ?, started_at = ?, extended_until_minutes = 90 WHERE id = 1",
            (project_id, datetime.now().isoformat()),
        )


def extend_timer(new_cap_minutes):
    with _conn() as c:
        c.execute(
            "UPDATE timer_state SET extended_until_minutes = ? WHERE id = 1",
            (new_cap_minutes,),
        )


def clear_timer():
    with _conn() as c:
        c.execute("UPDATE timer_state SET project_id = NULL, started_at = NULL, extended_until_minutes = 90 WHERE id = 1")


# ---------- Reflection / Stats ----------
def get_reflection_stats():
    """
    Returns high-level stats for the current reflection screen.

    Note:
    - total_hours_logged only counts positive session hours.
    - Corrections/subtractions are ignored for total effort.
    """
    with _conn() as c:
        total_hours = c.execute(
            """
            SELECT COALESCE(SUM(hours), 0)
            FROM sessions
            WHERE hours > 0
            """
        ).fetchone()[0]

        total_sessions = c.execute(
            """
            SELECT COUNT(*)
            FROM sessions
            WHERE hours > 0
            """
        ).fetchone()[0]

        active_bosses = c.execute(
            "SELECT COUNT(*) FROM projects WHERE status = 'active'"
        ).fetchone()[0]

        completed_bosses = c.execute(
            "SELECT COUNT(*) FROM projects WHERE status = 'completed'"
        ).fetchone()[0]

        failed_bosses = c.execute(
            "SELECT COUNT(*) FROM projects WHERE status = 'failed'"
        ).fetchone()[0]

        abandoned_bosses = c.execute(
            "SELECT COUNT(*) FROM projects WHERE status = 'abandoned'"
        ).fetchone()[0]

        significant_growth_events = c.execute(
            "SELECT COUNT(*) FROM emotional_clicks"
        ).fetchone()[0]

        return {
            "total_hours": total_hours,
            "total_sessions": total_sessions,
            "active_bosses": active_bosses,
            "completed_bosses": completed_bosses,
            "failed_bosses": failed_bosses,
            "abandoned_bosses": abandoned_bosses,
            "significant_growth_events": significant_growth_events,
        }


def get_completed_projects(limit=10):
    """Returns recently completed bosses for the Hall/Reflection preview."""
    with _conn() as c:
        return c.execute(
            """
            SELECT id, name, total_hours, hours_logged, deadline, created_at, closed_at
            FROM projects
            WHERE status = 'completed'
            ORDER BY closed_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
