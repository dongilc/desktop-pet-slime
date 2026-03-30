import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu

from core.pet_window import PetWindow
from core.settings import Settings
from character.slime import SlimeCharacter
from monitors.system_monitor import SystemMonitor
from monitors.activity_monitor import ActivityMonitor
from features.reminders import ReminderManager, ReminderDialog
from features.notifications import TooltipBubble


def create_tray_icon() -> QIcon:
    """Create a simple slime icon programmatically."""
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setPen(QPen(QColor(60, 160, 60), 2))
    painter.setBrush(QBrush(QColor(100, 210, 100)))
    painter.drawEllipse(8, 12, 48, 40)

    painter.setPen(QPen(QColor(0, 0, 0, 0)))
    painter.setBrush(QBrush(QColor(40, 40, 40)))
    painter.drawEllipse(22, 24, 6, 8)
    painter.drawEllipse(36, 24, 6, 8)

    painter.setBrush(QBrush(QColor(255, 255, 255, 150)))
    painter.drawEllipse(18, 18, 10, 7)

    painter.end()
    return QIcon(pixmap)


class PetApp:
    """Main application orchestrator."""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        self.settings = Settings()
        self.slime = SlimeCharacter()

        # Main pet window
        self.window = PetWindow(self.slime)

        # Restore position
        pos = self.settings.get("slime_position")
        if pos:
            self.window.move(pos[0], pos[1])

        # Apply saved size
        size_pct = self.settings.get("size_percent", 100)
        if size_pct != 100:
            new_size = int(250 * size_pct / 100)
            self.window.WIDGET_SIZE = new_size
            self.window.setFixedSize(new_size, new_size)

        # System monitor
        self.monitor = SystemMonitor()
        self.monitor.stats_updated.connect(self._on_stats)

        # Activity monitor
        self.activity = ActivityMonitor(
            break_interval_min=self.settings.get("break_interval_min", 45)
        )
        self.activity.break_needed.connect(self._on_break_needed)
        self.activity.idle_updated.connect(self._on_idle_updated)

        # Reminder manager
        self.reminders = ReminderManager()
        self.reminders.reminder_fired.connect(self._on_reminder)

        # Override pet_window callbacks
        self.window._add_reminder = self._add_reminder_dialog
        self.window._open_settings = self._open_settings_dialog

        # System tray
        self._setup_tray()

        self._idle_seconds = 0.0
        self._battery_warned = False
        self._active_bubbles = []

    def _setup_tray(self):
        self.tray = QSystemTrayIcon(create_tray_icon(), self.app)

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 8px;
                padding: 5px;
                font-size: 13px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #4a9eff;
            }
            QMenu::separator {
                height: 1px;
                background: #555;
                margin: 4px 10px;
            }
        """)

        show_action = menu.addAction("Show/Hide Pet")
        show_action.triggered.connect(self._toggle_visibility)

        info_action = menu.addAction("System Info")
        info_action.triggered.connect(self.window._show_system_info)

        game_action = menu.addAction("Mini Game")
        game_action.triggered.connect(self.window._open_minigame)

        reminder_action = menu.addAction("Add Reminder")
        reminder_action.triggered.connect(self._add_reminder_dialog)

        menu.addSeparator()

        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(self._open_settings_dialog)

        menu.addSeparator()

        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self._quit)

        self.tray.setContextMenu(menu)
        self.tray.setToolTip("Desktop Pet Slime")
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _toggle_visibility(self):
        if self.window.isVisible():
            self.window.hide()
        else:
            self.window.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._toggle_visibility()

    def _on_stats(self, cpu, ram, disk, net_bps, battery):
        self.slime.set_system_stats(
            cpu, ram, disk, net_bps, battery, self._idle_seconds
        )

        # Battery warning (only warn once per charge cycle)
        if battery is not None and battery < 20 and not self._battery_warned:
            self._battery_warned = True
            self._show_bubble(f"Battery low: {battery:.0f}%!")
        elif battery is not None and battery > 30:
            self._battery_warned = False

    def _on_idle_updated(self, idle_seconds):
        self._idle_seconds = idle_seconds

    def _on_break_needed(self):
        self.slime.request_stretch()
        self._show_bubble("Time to stretch! Take a break~")

    def _on_reminder(self, message):
        self._show_bubble(f"Reminder: {message}")
        self.slime.jiggle.trigger(10.0)

    def _add_reminder_dialog(self):
        dialog = ReminderDialog(self.window)
        if dialog.exec():
            if dialog.result_message:
                self.reminders.add(dialog.result_message,
                                   dialog.result_minutes)
                self._show_bubble(
                    f"Reminder set: {dialog.result_minutes}min")

    def _open_settings_dialog(self):
        from features.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.window)

        # Load current settings
        dialog.break_spin.setValue(
            self.settings.get("break_interval_min", 45))
        dialog.size_slider.setValue(
            self.settings.get("size_percent", 100))

        topmost = self.settings.get("always_on_top", True)
        dialog.topmost_check.setChecked(topmost)

        if dialog.exec():
            # Save break interval
            self.settings.set("break_interval_min", dialog.result_break_min)
            self.activity.break_interval = dialog.result_break_min * 60

            # Save and apply size
            self.settings.set("size_percent", dialog.result_size_percent)
            new_size = int(250 * dialog.result_size_percent / 100)
            self.window.WIDGET_SIZE = new_size
            self.window.setFixedSize(new_size, new_size)

            # Always on top
            self.settings.set("always_on_top", dialog.result_topmost)
            flags = (Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
            if dialog.result_topmost:
                flags |= Qt.WindowType.WindowStaysOnTopHint
            was_visible = self.window.isVisible()
            self.window.setWindowFlags(flags)
            self.window.setAttribute(
                Qt.WidgetAttribute.WA_TranslucentBackground)
            if was_visible:
                self.window.show()

            self._show_bubble("Settings saved!")

    def _show_bubble(self, message):
        # Clean up old bubbles
        self._active_bubbles = [b for b in self._active_bubbles
                                if b.isVisible()]
        bubble = TooltipBubble(message, None)
        bubble.show_above(self.window)
        self._active_bubbles.append(bubble)

    def _quit(self):
        # Save position
        pos = self.window.pos()
        self.settings.set("slime_position", [pos.x(), pos.y()])

        self.monitor.stop()
        self.tray.hide()
        self.app.quit()

    def run(self):
        self.window.show()
        self.monitor.start()
        return self.app.exec()
