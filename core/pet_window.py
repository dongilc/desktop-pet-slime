from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QWidget, QMenu

from character.slime import SlimeCharacter
from character.renderer import SlimeRenderer


class PetWindow(QWidget):
    """Transparent frameless window that displays the slime pet."""

    WIDGET_SIZE = 250

    def __init__(self, slime: SlimeCharacter):
        super().__init__()
        self.slime = slime
        self.renderer = SlimeRenderer()

        # Drag state
        self._drag_pos = None
        self._drag_start = None
        self._was_dragged = False

        self._setup_window()
        self._setup_timer()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(self.WIDGET_SIZE, self.WIDGET_SIZE)

        # Position at bottom-right of screen
        from PyQt6.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.width() - self.WIDGET_SIZE - 50,
                      geo.height() - self.WIDGET_SIZE - 20)

    def _setup_timer(self):
        self._timer = QTimer(self)
        self._timer.setInterval(33)  # ~30 FPS
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        dt = 0.033
        cx = self.WIDGET_SIZE / 2
        cy = self.WIDGET_SIZE / 2
        self.slime.tick(dt, cx, cy)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        self.renderer.draw(painter, self.slime,
                           self.WIDGET_SIZE, self.WIDGET_SIZE,
                           widget_pos=self.pos())
        painter.end()

    # --- Mouse interaction ---

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint()
            self._drag_start = event.globalPosition().toPoint()
            self._was_dragged = False

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

            if self._drag_start:
                total = event.globalPosition().toPoint() - self._drag_start
                if abs(total.x()) > 5 or abs(total.y()) > 5:
                    self._was_dragged = True

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self._was_dragged:
                self.slime.pet()
            self._drag_pos = None
            self._drag_start = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_minigame()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
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

        info_action = menu.addAction("System Info")
        info_action.triggered.connect(self._show_system_info)

        game_action = menu.addAction("Mini Game")
        game_action.triggered.connect(self._open_minigame)

        reminder_action = menu.addAction("Add Reminder")
        reminder_action.triggered.connect(self._add_reminder)

        menu.addSeparator()

        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(self._open_settings)

        menu.addSeparator()

        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self._quit)

        menu.exec(event.globalPos())

    def _show_system_info(self):
        from features.system_info_dialog import SystemInfoDialog
        dialog = SystemInfoDialog(self.slime, self)
        dialog.exec()

    def _open_minigame(self):
        from features.minigame import SlimeFeedGame
        game = SlimeFeedGame(self.slime, self)
        game.exec()

    def _add_reminder(self):
        from features.reminders import ReminderDialog
        dialog = ReminderDialog(self)
        dialog.exec()

    def _open_settings(self):
        from features.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec()

    def _quit(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()
