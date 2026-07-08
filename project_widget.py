"""Single project row: name, inverted progress bar, +/- buttons."""
from datetime import date
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar, QPushButton,
)
from PySide6.QtCore import Signal, Qt


class ProjectWidget(QWidget):
    log_requested = Signal(int, str)  # (project_id, mode: 'add' | 'subtract')

    def __init__(self, project_row):
        super().__init__()
        self.project_id = project_row["id"]
        self.total_hours = project_row["total_hours"]
        self.hours_logged = project_row["hours_logged"]
        self.deadline = date.fromisoformat(project_row["deadline"])
        self.name = project_row["name"]

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 6, 8, 6)

        # Row 1: name + deadline
        top = QHBoxLayout()
        self.name_label = QLabel(f"<b>{self.name}</b>")
        self.deadline_label = QLabel()
        self.deadline_label.setAlignment(Qt.AlignRight)
        top.addWidget(self.name_label)
        top.addWidget(self.deadline_label)
        outer.addLayout(top)

        # Row 2: progress bar
        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)  # use 0.1% resolution
        self.bar.setTextVisible(True)
        outer.addWidget(self.bar)

        # Row 3: buttons + hours text
        bottom = QHBoxLayout()
        self.hours_label = QLabel()
        self.plus_btn = QPushButton("+ Log hours")
        self.minus_btn = QPushButton("− Correct")
        self.plus_btn.clicked.connect(
            lambda: self.log_requested.emit(self.project_id, "add")
        )
        self.minus_btn.clicked.connect(
            lambda: self.log_requested.emit(self.project_id, "subtract")
        )
        bottom.addWidget(self.hours_label)
        bottom.addStretch()
        bottom.addWidget(self.minus_btn)
        bottom.addWidget(self.plus_btn)
        outer.addLayout(bottom)

    def refresh(self):
        # Inverted bar: starts at 100%, drops to 0%
        remaining_pct = max(0.0, 100.0 - (self.hours_logged / self.total_hours * 100.0))
        self.bar.setValue(int(remaining_pct * 10))
        self.bar.setFormat(f"{remaining_pct:.1f}% remaining (boss HP)")

        self.hours_label.setText(
            f"{self.hours_logged:.1f} / {self.total_hours:.0f} hrs logged"
        )

        days_left = (self.deadline - date.today()).days
        if days_left < 0:
            self.deadline_label.setText(
                f"<span style='color:#c0392b'><b>OVERDUE</b></span>"
            )
            self.bar.setStyleSheet(
                "QProgressBar::chunk { background-color: #c0392b; }"
            )
        elif days_left <= 7:
            self.deadline_label.setText(
                f"<span style='color:#e67e22'>{days_left}d left · {self.deadline}</span>"
            )
            self.bar.setStyleSheet(
                "QProgressBar::chunk { background-color: #e67e22; }"
            )
        else:
            self.deadline_label.setText(f"{days_left}d left · {self.deadline}")
            self.bar.setStyleSheet(
                "QProgressBar::chunk { background-color: #27ae60; }"
            )

    def update_hours(self, new_hours: float):
        self.hours_logged = new_hours
        self.refresh()