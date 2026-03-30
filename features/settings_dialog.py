import sys
import os
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QPushButton, QCheckBox, QGroupBox, QSlider, QFrame
)


STARTUP_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "DesktopPetSlime"


def _get_exe_path() -> str:
    """Get the path to use for auto-start."""
    if getattr(sys, 'frozen', False):
        return sys.executable
    return f'"{sys.executable}" "{os.path.abspath("main.py")}"'


def is_autostart_enabled() -> bool:
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_KEY,
                             0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False


def set_autostart(enabled: bool):
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_REG_KEY,
                             0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ,
                              _get_exe_path())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception:
        pass


class SettingsDialog(QDialog):
    """Settings dialog for the desktop pet."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(350, 380)
        self.setStyleSheet("""
            QDialog {
                background-color: #2a2a3d;
                color: #ffffff;
            }
            QLabel {
                color: #ddddee;
                font-size: 13px;
            }
            QGroupBox {
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 18px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
            }
            QSpinBox {
                background-color: #3d3d55;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 5px;
                font-size: 13px;
            }
            QCheckBox {
                color: #ddddee;
                font-size: 13px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #666;
                background-color: #3d3d55;
            }
            QCheckBox::indicator:checked {
                background-color: #4a9eff;
                border-color: #4a9eff;
            }
            QPushButton {
                background-color: #4a9eff;
                color: white;
                padding: 10px 25px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #5aafff;
            }
            QPushButton#cancelBtn {
                background-color: #555;
            }
            QPushButton#cancelBtn:hover {
                background-color: #666;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #3d3d55;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #4a9eff;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #4a9eff;
                border-radius: 3px;
            }
        """)

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Title
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Break reminder group
        break_group = QGroupBox("Break Reminder")
        break_layout = QVBoxLayout(break_group)

        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Remind every"))
        self.break_spin = QSpinBox()
        self.break_spin.setRange(5, 120)
        self.break_spin.setValue(45)
        self.break_spin.setSuffix(" min")
        h1.addWidget(self.break_spin)
        break_layout.addLayout(h1)

        layout.addWidget(break_group)

        # Display group
        display_group = QGroupBox("Display")
        display_layout = QVBoxLayout(display_group)

        h2 = QHBoxLayout()
        h2.addWidget(QLabel("Slime Size"))
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(50, 150)
        self.size_slider.setValue(100)
        self.size_label = QLabel("100%")
        self.size_slider.valueChanged.connect(
            lambda v: self.size_label.setText(f"{v}%"))
        h2.addWidget(self.size_slider)
        h2.addWidget(self.size_label)
        display_layout.addLayout(h2)

        self.topmost_check = QCheckBox("Always on top")
        self.topmost_check.setChecked(True)
        display_layout.addWidget(self.topmost_check)

        layout.addWidget(display_group)

        # System group
        sys_group = QGroupBox("System")
        sys_layout = QVBoxLayout(sys_group)

        self.autostart_check = QCheckBox("Start with Windows")
        self.autostart_check.setChecked(is_autostart_enabled())
        sys_layout.addWidget(self.autostart_check)

        layout.addWidget(sys_group)

        # Buttons
        layout.addStretch()
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        # Store results
        self.result_break_min = None
        self.result_autostart = None
        self.result_topmost = None
        self.result_size_percent = None

    def accept(self):
        self.result_break_min = self.break_spin.value()
        self.result_autostart = self.autostart_check.isChecked()
        self.result_topmost = self.topmost_check.isChecked()
        self.result_size_percent = self.size_slider.value()

        # Apply auto-start
        set_autostart(self.result_autostart)

        super().accept()
