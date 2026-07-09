"""Single project row: name, inverted progress bar, +/-/timer/delete buttons."""
from datetime import date
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar, QPushButton,
)
from PySide6.QtCore import Signal, Qt


class ProjectWidget(QWidget):
    log_requested = Signal(int, str)          # (project_id, 'add' | 'subtract')
    timer_toggle_requested = Signal(int)      # project_id
    delete_requested = Signal(int, str)       # (project_id, name)

    def __init__(self, project_row):
        super().__init__()
        self.project_id = project_row["id"]
        self.total_hours = project_row["total_hours"]
        self.hours_logged = project_row["hours_logged"]
        self.deadline = date.fromisoformat(project_row["deadline"])
        self.name = project_row["name"]
        self._timer_running = False
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)

        # Row 1: name (bigger) + deadline
        top = QHBoxLayout()
        self.name_label = QLabel(
            f"<span style='font-size:18pt; font-weight:bold;'>{self.name}</span>"
        )
        self.deadline_label = QLabel()
        self.deadline_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        top.addWidget(self.name_label)
        top.addWidget(self.deadline_label)
        outer.addLayout(top)

        # Row 2: progress bar
        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)
        self.bar.setTextVisible(True)
        self.bar.setMinimumHeight(22)
        outer.addWidget(self.bar)

        # Row 3: hours label + buttons
        bottom = QHBoxLayout()
        self.hours_label = QLabel()
        self.timer_btn = QPushButton("▶ Start timer")
        self.plus_btn = QPushButton("+ Log hours")
        self.minus_btn = QPushButton("− Correct")
        self.delete_btn = QPushButton("🗑")
        self.delete_btn.setToolTip("Delete project")
        self.delete_btn.setFixedWidth(36)

        self.timer_btn.clicked.connect(
            lambda: self.timer_toggle_requested.emit(self.project_id)
        )
        self.plus_btn.clicked.connect(
            lambda: self.log_requested.emit(self.project_id, "add")
        )
        self.minus_btn.clicked.connect(
            lambda: self.log_requested.emit(self.project_id, "subtract")
        )
        self.delete_btn.clicked.connect(
            lambda: self.delete_requested.emit(self.project_id, self.name)
        )

        bottom.addWidget(self.hours_label)
        bottom.addStretch()
        bottom.addWidget(self.timer_btn)
        bottom.addWidget(self.minus_btn)
        bottom.addWidget(self.plus_btn)
        bottom.addWidget(self.delete_btn)
        outer.addLayout(bottom)

    def refresh(self):
        remaining_pct = max(0.0, 100.0 - (self.hours_logged / self.total_hours * 100.0))
        self.bar.setValue(int(remaining_pct * 10))
        self.bar.setFormat(f"{remaining_pct:.1f}% remaining (boss HP)")
        self.hours_label.setText(f"{self.hours_logged:.1f} / {self.total_hours:.0f} hrs logged")

        days_left = (self.deadline - date.today()).days
        if days_left < 0:
            self.deadline_label.setText("<span style='color:#c0392b'><b>OVERDUE</b></span>")
            self.bar.setStyleSheet("QProgressBar::chunk { background-color: #c0392b; }")
        elif days_left <= 7:
            self.deadline_label.setText(
                f"<span style='color:#e67e22'>{days_left}d left · {self.deadline}</span>"
            )
            self.bar.setStyleSheet("QProgressBar::chunk { background-color: #e67e22; }")
        else:
            self.deadline_label.setText(f"{days_left}d left · {self.deadline}")
            self.bar.setStyleSheet("QProgressBar::chunk { background-color: #27ae60; }")

    def update_hours(self, new_hours):
        self.hours_logged = new_hours
        self.refresh()

    def set_timer_display(self, running: bool, elapsed_text: str = ""):
        self._timer_running = running
        if running:
            self.timer_btn.setText(f"⏹ Stop ({elapsed_text})")
            self.timer_btn.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold;")
        else:
            self.timer_btn.setText("▶ Start timer")
            self.timer_btn.setStyleSheet("")