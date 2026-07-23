"""Small modal dialogs: add project, log hours."""
from datetime import date, timedelta
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QDoubleSpinBox, QDateEdit,
    QDialogButtonBox, QMessageBox, QLabel
)
from PySide6.QtCore import QDate


class AddProjectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        form = QFormLayout(self)

        self.name = QLineEdit()
        self.name.setPlaceholderText("e.g. Neural Networks")

        self.hours = QDoubleSpinBox()
        self.hours.setRange(1, 10000)
        self.hours.setValue(100)
        self.hours.setSuffix(" hrs")

        self.deadline = QDateEdit()
        self.deadline.setCalendarPopup(True)
        self.deadline.setDate(QDate.currentDate().addDays(45))
        self.deadline.setMinimumDate(QDate.currentDate().addDays(1))

        form.addRow("Name:", self.name)
        form.addRow("Total hours:", self.hours)
        form.addRow("Deadline:", self.deadline)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._validate_accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _validate_accept(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "Missing", "Name required.")
            return
        self.accept()

    def values(self):
        return (
            self.name.text().strip(),
            self.hours.value(),
            self.deadline.date().toString("yyyy-MM-dd"),
        )


class LogHoursDialog(QDialog):
    def __init__(self, project_name: str, mode: str, parent=None):
        """mode = 'add' or 'subtract'"""
        super().__init__(parent)
        self.mode = mode
        self.setWindowTitle(f"{'Log' if mode == 'add' else 'Correct'} — {project_name}")
        form = QFormLayout(self)

        self.hours = QDoubleSpinBox()
        self.hours.setRange(0.1, 24)
        self.hours.setSingleStep(0.5)
        self.hours.setValue(1.0)
        self.hours.setSuffix(" hrs")

        label = "Hours to add:" if mode == "add" else "Hours to remove (correction):"
        form.addRow(label, self.hours)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def value(self):
        return self.hours.value()


class EditProjectDialog(QDialog):
    def __init__(self, current_name, current_total_hours, hours_logged, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit — {current_name}")

        self._hours_logged = hours_logged

        form = QFormLayout(self)

        self.name = QLineEdit()
        self.name.setText(current_name)

        self.hours = QDoubleSpinBox()
        self.hours.setRange(0.1, 10000)
        self.hours.setValue(current_total_hours)
        self.hours.setSuffix(" hrs")
        self.hours.setDecimals(1)

        # Warn: cannot go below hours already logged
        warning = QLabel(
            f"You have already logged {hours_logged:.1f} hrs.\n"
            f"Total cannot be reduced below that.\n\n"
            f"Note: deadline cannot be edited. That was the commitment."
        )
        warning.setStyleSheet("color: gray; font-size: 10pt;")
        warning.setWordWrap(True)

        form.addRow("Name:", self.name)
        form.addRow("Total hours:", self.hours)
        form.addRow(warning)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._validate_accept)
        btns.rejected.connect(self.reject)
        form.addRow(btns)

    def _validate_accept(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "Missing", "Name required.")
            return

        if self.hours.value() < self._hours_logged:
            QMessageBox.warning(
                self,
                "Invalid",
                f"Total hours cannot be less than hours already logged "
                f"({self._hours_logged:.1f} hrs).",
            )
            return

        self.accept()

    def values(self):
        return (
            self.name.text().strip(),
            self.hours.value(),
        )
