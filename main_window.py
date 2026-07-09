"""Main window: project list + meta-bar + emotional button + timer."""
from datetime import date, datetime
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QScrollArea, QMessageBox, QFrame,
)
from PySide6.QtCore import Qt, QTimer

import db
import growth
from config import MAX_ACTIVE_PROJECTS, TIMER_PROMPT_MINUTES, TIMER_EXTEND_MINUTES
from dialogs import AddProjectDialog, LogHoursDialog
from project_widget import ProjectWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProgressBar")
        self.resize(620, 720)

        self.project_widgets = {}
        self.active_timer_project_id = None
        self.timer_prompted = False

        db.init_db()
        growth.check_and_apply_reset()
        self._check_overdue_projects()

        self._build_ui()
        self._reload_projects()
        self._refresh_meta_bar()
        self._recover_timer()

        # Tick every second to update running timer display
        self.tick = QTimer(self)
        self.tick.setInterval(1000)
        self.tick.timeout.connect(self._on_tick)
        self.tick.start()

    # ---------- UI ----------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # Meta-bar
        meta_frame = QFrame()
        meta_frame.setFrameShape(QFrame.StyledPanel)
        meta_layout = QVBoxLayout(meta_frame)

        meta_layout.addWidget(QLabel(
            "<span style='font-size:21pt; font-weight:bold;'>Growth this cycle</span>"
        ))

        self.meta_bar = QProgressBar()
        self.meta_bar.setRange(0, 1000)
        self.meta_bar.setTextVisible(True)
        self.meta_bar.setMinimumHeight(26)
        meta_layout.addWidget(self.meta_bar)

        meta_btn_row = QHBoxLayout()
        self.emotional_btn = QPushButton("I grew emotionally / financially today")
        self.emotional_btn.clicked.connect(self._on_emotional_click)
        meta_btn_row.addWidget(self.emotional_btn)
        meta_layout.addLayout(meta_btn_row)

        root.addWidget(meta_frame)

        # Projects header
        header_row = QHBoxLayout()
        header_row.addWidget(QLabel(
            "<span style='font-size:21pt; font-weight:bold;'>Active projects</span>"
        ))
        header_row.addStretch()
        self.add_btn = QPushButton("+ New project")
        self.add_btn.clicked.connect(self._on_add_project)
        header_row.addWidget(self.add_btn)
        root.addLayout(header_row)

        # Scrollable list
        self.projects_container = QWidget()
        self.projects_layout = QVBoxLayout(self.projects_container)
        self.projects_layout.setAlignment(Qt.AlignTop)

        scroll = QScrollArea()
        scroll.setWidget(self.projects_container)
        scroll.setWidgetResizable(True)
        root.addWidget(scroll)

    # ---------- Reload ----------
    def _reload_projects(self):
        for i in reversed(range(self.projects_layout.count())):
            w = self.projects_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        self.project_widgets.clear()

        rows = db.get_active_projects()
        if not rows:
            empty = QLabel("<i>No active projects. Click '+ New project' to add one.</i>")
            empty.setAlignment(Qt.AlignCenter)
            self.projects_layout.addWidget(empty)
            return

        for row in rows:
            w = ProjectWidget(row)
            w.log_requested.connect(self._on_log_request)
            w.timer_toggle_requested.connect(self._on_timer_toggle)
            w.delete_requested.connect(self._on_delete_request)
            self.projects_layout.addWidget(w)
            self.project_widgets[row["id"]] = w

        # Restore timer visual if one is running
        if self.active_timer_project_id in self.project_widgets:
            self._update_timer_display()

    def _refresh_meta_bar(self):
        pct = growth.current_percent()
        self.meta_bar.setValue(int(pct * 10))
        today = date.today()
        reset_year = today.year if today < date(today.year, 5, 28) else today.year + 1
        self.meta_bar.setFormat(f"{pct:.1f}% — Resets May 28, {reset_year}")

    # ---------- Add / Log / Emotional ----------
    def _on_add_project(self):
        if db.get_active_count() >= MAX_ACTIVE_PROJECTS:
            QMessageBox.warning(
                self, "Too many projects",
                f"Max {MAX_ACTIVE_PROJECTS} active projects. Finish, fail, or delete one first.",
            )
            return
        dlg = AddProjectDialog(self)
        if dlg.exec():
            name, hours, deadline = dlg.values()
            db.add_project(name, hours, deadline)
            self._reload_projects()

    def _on_log_request(self, project_id, mode):
        pw = self.project_widgets[project_id]
        dlg = LogHoursDialog(pw.name, mode, self)
        if not dlg.exec():
            return
        delta = dlg.value() if mode == "add" else -dlg.value()
        self._apply_hours(project_id, delta)

    def _apply_hours(self, project_id, delta):
        """Shared logic: update hours, log session, meta-bar, defeat check."""
        pw = self.project_widgets[project_id]
        new_hours = max(0.0, pw.hours_logged + delta)
        db.update_project_hours(project_id, new_hours)
        db.log_session(project_id, delta)
        pw.update_hours(new_hours)

        if delta > 0:
            growth.add_hours(delta)

        if new_hours >= pw.total_hours:
            self._on_project_defeated(project_id, pw.name)

        self._refresh_meta_bar()
        self._check_fireworks()

    def _on_emotional_click(self):
        ok, pct, msg = growth.try_emotional_click()
        self._refresh_meta_bar()
        if not ok:
            QMessageBox.information(self, "Nope", msg)
        else:
            self._check_fireworks()

    # ---------- Delete ----------
    def _on_delete_request(self, project_id, name):
        reply = QMessageBox.question(
            self,
            "Delete project?",
            f"Delete '{name}'?\n\n"
            f"It will be archived as 'abandoned' — no growth bonus, no penalty.\n"
            f"This can't be undone from the UI.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        # If timer is running on this project, stop it silently first
        if self.active_timer_project_id == project_id:
            db.clear_timer()
            self.active_timer_project_id = None
            self.timer_prompted = False
        db.close_project(project_id, "abandoned")
        self._reload_projects()

    # ---------- Timer ----------
    def _on_timer_toggle(self, project_id):
        if self.active_timer_project_id is None:
            # Start
            db.start_timer(project_id)
            self.active_timer_project_id = project_id
            self.timer_prompted = False
            self._update_timer_display()
        elif self.active_timer_project_id == project_id:
            # Stop this timer, log hours
            self._stop_timer_and_log()
        else:
            # Another timer running
            other = self.project_widgets.get(self.active_timer_project_id)
            other_name = other.name if other else "another project"
            QMessageBox.warning(
                self, "Timer already running",
                f"Stop the timer on '{other_name}' before starting a new one.",
            )

    def _recover_timer(self):
        row = db.get_timer()
        if row and row["project_id"] and row["started_at"]:
            self.active_timer_project_id = row["project_id"]
            started = datetime.fromisoformat(row["started_at"])
            elapsed_min = (datetime.now() - started).total_seconds() / 60
            reply = QMessageBox.question(
                self,
                "Timer was running",
                f"A timer was running when you closed the app "
                f"({elapsed_min:.0f} min elapsed).\n\n"
                f"Log these hours? (Yes = log, No = discard)",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                hours = min(elapsed_min / 60.0, 8.0)  # sanity cap
                self._apply_hours(self.active_timer_project_id, hours)
            db.clear_timer()
            self.active_timer_project_id = None

    def _stop_timer_and_log(self):
        row = db.get_timer()
        if not row or not row["started_at"]:
            return
        started = datetime.fromisoformat(row["started_at"])
        elapsed_hours = (datetime.now() - started).total_seconds() / 3600.0
        pid = self.active_timer_project_id
        db.clear_timer()
        self.active_timer_project_id = None
        self.timer_prompted = False
        pw = self.project_widgets.get(pid)
        if pw:
            pw.set_timer_display(False)
        if elapsed_hours >= 0.01:  # ignore accidental sub-30-sec clicks
            self._apply_hours(pid, round(elapsed_hours, 2))

    def _on_tick(self):
        if self.active_timer_project_id is None:
            return
        self._update_timer_display()
        self._maybe_prompt_timer_cap()

    def _update_timer_display(self):
        row = db.get_timer()
        if not row or not row["started_at"]:
            return
        started = datetime.fromisoformat(row["started_at"])
        secs = int((datetime.now() - started).total_seconds())
        hh, mm, ss = secs // 3600, (secs % 3600) // 60, secs % 60
        elapsed = f"{hh:02d}:{mm:02d}:{ss:02d}"
        pw = self.project_widgets.get(self.active_timer_project_id)
        if pw:
            pw.set_timer_display(True, elapsed)

    def _maybe_prompt_timer_cap(self):
        row = db.get_timer()
        if not row or not row["started_at"]:
            return
        started = datetime.fromisoformat(row["started_at"])
        elapsed_min = (datetime.now() - started).total_seconds() / 60
        cap = row["extended_until_minutes"]
        if elapsed_min >= cap and not self.timer_prompted:
            self.timer_prompted = True
            pw = self.project_widgets.get(self.active_timer_project_id)
            name = pw.name if pw else "project"
            reply = QMessageBox.question(
                self,
                "Still working?",
                f"Timer on '{name}' has been running {elapsed_min:.0f} minutes.\n\n"
                f"Still working? (Yes = keep going another {TIMER_EXTEND_MINUTES} min, "
                f"No = stop and log)",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply == QMessageBox.Yes:
                db.extend_timer(int(cap + TIMER_EXTEND_MINUTES))
                self.timer_prompted = False
            else:
                self._stop_timer_and_log()

    # ---------- Endings ----------
    def _on_project_defeated(self, project_id, name):
        db.close_project(project_id, "completed")
        growth.add_project_defeat_bonus()
        QMessageBox.information(self, "Boss defeated 🗡️",
                                f"'{name}' completed. +2% growth bonus applied.")
        # Kill timer if it was on this project
        if self.active_timer_project_id == project_id:
            db.clear_timer()
            self.active_timer_project_id = None
        self._reload_projects()

    def _check_overdue_projects(self):
        rows = db.get_active_projects()
        today = date.today()
        failed = []
        for row in rows:
            deadline = date.fromisoformat(row["deadline"])
            if today > deadline and row["hours_logged"] < row["total_hours"]:
                db.close_project(row["id"], "failed")
                failed.append(row["name"])
        if failed:
            QMessageBox.critical(
                self, "Projects failed",
                "The following projects blew past their deadline and were auto-archived as FAILED:\n\n"
                + "\n".join(f"• {n}" for n in failed)
                + "\n\nNo growth bonus. No extensions. Do better.",
            )

    def _check_fireworks(self):
        if growth.current_percent() >= 100.0:
            QMessageBox.information(
                self, "🎆 FIREWORKS 🎆",
                "You hit 100% growth for the cycle.\n\n(V2: actual fireworks animation.)",
            )