from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect


class TooltipBubble(QWidget):
    """A floating speech bubble notification above the pet."""

    def __init__(self, message: str, parent=None, duration_ms=3000):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._setup_ui(message)

        # Auto-close
        QTimer.singleShot(duration_ms, self._fade_out)

    def _setup_ui(self, message):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                background-color: rgba(45, 45, 45, 220);
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                padding: 10px 15px;
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 40);
            }
        """)
        layout.addWidget(self.label)
        self.adjustSize()

        # Opacity effect
        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity)

    def show_above(self, pet_widget):
        """Position above the pet widget and show."""
        pet_pos = pet_widget.pos()
        x = pet_pos.x() + pet_widget.width() // 2 - self.width() // 2
        y = pet_pos.y() - self.height() - 10
        self.move(x, y)
        self.show()

    def _fade_out(self):
        self._anim = QPropertyAnimation(self._opacity, b"opacity")
        self._anim.setDuration(500)
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(self.close)
        self._anim.start()
