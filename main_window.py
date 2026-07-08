"""Main window: project list + meta-bar + emotional button."""
from datetime import date
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QScrollArea, QMessageBox, QFrame,
)
from PySide6.QtCore import Qt

import db
import growth
from config import MAX_ACTIVE_PROJECTS
from dialogs import AddProjectDialog, LogHoursDialog
from project_widget import ProjectWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ProgressBar")
        self.resize(560, 640)

        self.project_widgets = {}  # id -> ProjectWidget

        db.init_db()
        growth.check_and_apply_reset()
        self._check_overdue_projects()

        self._build_ui()
        self._reload_projects()
        self._refresh_meta_bar()

    # ---------- UI ----------
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # Meta-bar section
        meta_frame = QFrame()
        meta_frame.setFrameShape(QFrame.StyledPanel)
        meta_layout = QVBoxLayout(meta_frame)

        title = QLabel("<h2>Growth this cycle</h2>")
        meta_layout.addWidget(title)

        self.meta_bar = QProgressBar()
        self.meta_bar.setRange(0, 1000)
        self.meta_bar.setTextVisible(True)
        meta_layout.addWidget(self.meta_bar)

        meta_btn_row = QHBoxLayout()
        self.emotional_btn = QPushButton("I grew emotionally / financially today")
        self.emotional_btn.clicked.connect(self._on_emotional_click)
        meta_btn_row.addWidget(self.emotional_btn)
        meta_layout.addLayout(meta_btn_row)

        root.addWidget(meta_frame)

        # Projects section
        header_row = QHBoxLayout()
        header_row.addWidget(QLabel("<h2>Active projects</h2>"))
        header_row.addStretch()
        self.add_btn = QPushButton("+ New project")
        self.add_btn.clicked.connect(self._on_add_project)
        header_row.addWidget(self.add_btn)
        root.addLayout(header_row)

        # Scroll area for projects
        self.projects_container = QWidget()
        self.projects_layout = QVBoxLayout(self.projects_container)
        self.projects_layout.setAlignment(Qt.AlignTop)

        scroll = QScrollArea()
        scroll.setWidget(self.projects_container)
        scroll.setWidgetResizable(True)
        root.addWidget(scroll)

    # ---------- Reload ----------
    def _reload_projects(self):
        # Clear
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
            self.projects_layout.addWidget(w)
            self.project_widgets[row["id"]] = w

    def _refresh_meta_bar(self):
        pct = growth.current_percent()
        self.meta_bar.setValue(int(pct * 10))
        self.meta_bar.setFormat(f"{pct:.1f}% — cycle resets May 28")

    # ---------- Handlers ----------
    def _on_add_project(self):
        if db.get_active_count() >= MAX_ACTIVE_PROJECTS:
            QMessageBox.warning(
                self,
                "Too many projects",
                f"Max {MAX_ACTIVE_PROJECTS} active projects. Finish or fail one first.\n"
                f"(Focus is the point of this app.)",
            )
            return
        dlg = AddProjectDialog(self)
        if dlg.exec():
            name, hours, deadline = dlg.values()
            db.add_project(name, hours, deadline)
            self._reload_projects()

    def _on_log_request(self, project_id: int, mode: str):
        pw = self.project_widgets[project_id]
        dlg = LogHoursDialog(pw.name, mode, self)
        if not dlg.exec():
            return
        delta = dlg.value() if mode == "add" else -dlg.value()

        new_hours = max(0.0, pw.hours_logged + delta)
        db.update_project_hours(project_id, new_hours)
        db.log_session(project_id, delta)
        pw.update_hours(new_hours)

        # Meta-bar only rewards positive logging
        if delta > 0:
            growth.add_hours(delta)

        # Boss defeated?
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

    # ---------- Endings ----------
    def _on_project_defeated(self, project_id: int, name: str):
        db.close_project(project_id, "completed")
        growth.add_project_defeat_bonus()
        QMessageBox.information(
            self,
            "Boss defeated 🗡️",
            f"'{name}' completed. +2% growth bonus applied.",
        )
        self._reload_projects()

    def _check_overdue_projects(self):
        """Auto-fail projects past deadline that aren't done. No mercy."""
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
                self,
                "Projects failed",
                "The following projects blew past their deadline and were auto-archived as FAILED:\n\n"
                + "\n".join(f"• {n}" for n in failed)
                + "\n\nNo growth bonus. No extensions. Do better.",
            )

    def _check_fireworks(self):
        if growth.current_percent() >= 100.0:
            QMessageBox.information(
                self,
                "🎆 FIREWORKS 🎆",
                "You hit 100% growth for the cycle.\n\n"
                "(V2: actual fireworks animation goes here.)",
            )