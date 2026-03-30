import json
from datetime import datetime, timedelta
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QPushButton, QListWidget, QListWidgetItem
)


class Reminder:
    def __init__(self, message: str, minutes_from_now: int):
        self.message = message
        self.due_time = datetime.now() + timedelta(minutes=minutes_from_now)
        self.fired = False

    def is_due(self) -> bool:
        return not self.fired and datetime.now() >= self.due_time

    def to_dict(self):
        return {
            "message": self.message,
            "due_time": self.due_time.isoformat(),
            "fired": self.fired,
        }


class ReminderManager(QObject):
    reminder_fired = pyqtSignal(str)  # message

    def __init__(self, parent=None):
        super().__init__(parent)
        self.reminders: list[Reminder] = []

        self._timer = QTimer(self)
        self._timer.setInterval(30000)  # check every 30s
        self._timer.timeout.connect(self._check)
        self._timer.start()

    def add(self, message: str, minutes: int):
        self.reminders.append(Reminder(message, minutes))

    def _check(self):
        for r in self.reminders:
            if r.is_due():
                r.fired = True
                self.reminder_fired.emit(r.message)

        # Clean up fired reminders
        self.reminders = [r for r in self.reminders if not r.fired]


class ReminderDialog(QDialog):
    """Dialog for adding reminders."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Reminder")
        self.setFixedSize(320, 200)
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit, QSpinBox {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 6px;
                font-size: 13px;
            }
            QPushButton {
                background-color: #4a9eff;
                color: white;
                padding: 8px 20px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #5aafff;
            }
        """)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Message:"))
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("What to remind?")
        layout.addWidget(self.msg_input)

        h_layout = QHBoxLayout()
        h_layout.addWidget(QLabel("In"))
        self.minutes_input = QSpinBox()
        self.minutes_input.setRange(1, 999)
        self.minutes_input.setValue(30)
        h_layout.addWidget(self.minutes_input)
        h_layout.addWidget(QLabel("minutes"))
        layout.addLayout(h_layout)

        btn = QPushButton("Add Reminder")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

        self.result_message = None
        self.result_minutes = None

    def accept(self):
        self.result_message = self.msg_input.text()
        self.result_minutes = self.minutes_input.value()
        super().accept()
