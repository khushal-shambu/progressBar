
"""Reflection dialog: shows proof of growth for the current season."""

from datetime import date

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QScrollArea,
    QWidget,
)
from PySide6.QtCore import Qt

import db
import growth


class ReflectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Reflection")
        self.resize(560, 620)

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        root = QVBoxLayout(self)

        title = QLabel("Reflection Screen")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24pt; font-weight: bold;")
        root.addWidget(title)

        subtitle = QLabel("Proof that you are not standing still.")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 11pt; color: gray;")
        root.addWidget(subtitle)

        # Scroll area so this can grow later without ruining the dialog.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(content)
        root.addWidget(scroll)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        root.addWidget(close_btn)

    def _load_data(self):
        self._add_season_section()
        self._add_stats_section()
        self._add_completed_bosses_section()

    def _add_season_section(self):
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(frame)

        heading = QLabel("Current Season")
        heading.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(heading)

        season_label = QLabel(self._season_text())
        season_label.setStyleSheet("font-size: 12pt;")
        layout.addWidget(season_label)

        self.content_layout.addWidget(frame)

    def _add_stats_section(self):
        stats = db.get_reflection_stats()
        growth_pct = growth.current_percent()

        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(frame)

        heading = QLabel("Season Stats")
        heading.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(heading)

        stat_lines = [
            f"Growth achieved: {growth_pct:.1f}%",
            f"Total hours logged: {stats['total_hours']:.2f} hrs",
            f"Total work sessions logged: {stats['total_sessions']}",
            f"Active bosses: {stats['active_bosses']}",
            f"Bosses slain: {stats['completed_bosses']}",
            f"Failed bosses: {stats['failed_bosses']}",
            f"Abandoned bosses: {stats['abandoned_bosses']}",
            f"Significant growth events: {stats['significant_growth_events']}",
        ]

        for line in stat_lines:
            label = QLabel(line)
            label.setStyleSheet("font-size: 12pt;")
            layout.addWidget(label)

        self.content_layout.addWidget(frame)

    def _add_completed_bosses_section(self):
        completed = db.get_completed_projects(limit=10)

        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        layout = QVBoxLayout(frame)

        heading = QLabel("Recently Slain Bosses")
        heading.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(heading)

        if not completed:
            empty = QLabel(
                "No bosses slain yet.\n\n"
                "Complete a project and it will appear here."
            )
            empty.setStyleSheet("font-size: 12pt;")
            empty.setWordWrap(True)
            layout.addWidget(empty)

            self.content_layout.addWidget(frame)
            return

        for row in completed:
            boss_type = self._enemy_type_for_hours(row["total_hours"])
            closed_at = row["closed_at"][:10] if row["closed_at"] else "Unknown date"

            boss_label = QLabel(
                f"{boss_type} slain: {row['name']}\n"
                f"Hours: {row['hours_logged']:.1f} / {row['total_hours']:.0f} hrs\n"
                f"Completed: {closed_at}"
            )
            boss_label.setStyleSheet("font-size: 12pt; margin-bottom: 8px;")
            boss_label.setWordWrap(True)

            layout.addWidget(boss_label)

        self.content_layout.addWidget(frame)

    def _season_text(self):
        row = db.get_growth()
        cycle_start = date.fromisoformat(row["cycle_start"])
        reset_year = cycle_start.year + 1

        return f"May 28, {cycle_start.year} to May 28, {reset_year}"

    def _enemy_type_for_hours(self, total_hours):
        """
        Simple V1.5 boss classification.

        This is intentionally basic for now.
        Later we can make this more RPG-like.
        """
        if total_hours < 10:
            return "Goblin"
        if total_hours < 50:
            return "Bandit"
        if total_hours < 100:
            return "Ogre"
        if total_hours < 250:
            return "Dragon"
        return "Ancient Dragon"
