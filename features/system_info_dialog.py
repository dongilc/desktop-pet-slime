import psutil
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QRadialGradient, QPainterPath
from PyQt6.QtWidgets import QDialog

from character.slime import SlimeCharacter
from character.states import SlimeState


class SystemInfoDialog(QDialog):
    """A beautiful custom system info dialog with live bars."""

    def __init__(self, slime: SlimeCharacter, parent=None):
        super().__init__(parent)
        self.slime = slime
        self.setWindowTitle("System Info")
        self.setFixedSize(320, 420)

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self.update)
        self._timer.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        bg = QRadialGradient(160, 210, 300)
        bg.setColorAt(0, QColor(40, 40, 65))
        bg.setColorAt(1, QColor(25, 25, 40))
        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(QColor(0, 0, 0, 0)))
        painter.drawRect(0, 0, 320, 420)

        # Title
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = painter.font()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(0, 15, 320, 30),
                         Qt.AlignmentFlag.AlignCenter, "System Monitor")

        # Slime status
        state = self.slime.state
        color = self.slime.color
        painter.setPen(QPen(color))
        font.setPointSize(12)
        painter.setFont(font)
        painter.drawText(QRectF(0, 48, 320, 25),
                         Qt.AlignmentFlag.AlignCenter,
                         f"Slime Status: {state.name}")

        # Resource bars
        y_start = 90
        bar_data = [
            ("CPU", self.slime.cpu, QColor(100, 200, 255),
             QColor(255, 100, 100)),
            ("RAM", self.slime.ram, QColor(100, 255, 180),
             QColor(255, 180, 80)),
            ("Disk", self.slime.disk, QColor(180, 150, 255),
             QColor(255, 100, 150)),
        ]

        font.setPointSize(11)
        font.setBold(False)
        painter.setFont(font)

        for i, (label, value, color_low, color_high) in enumerate(bar_data):
            y = y_start + i * 65

            # Label
            painter.setPen(QPen(QColor(200, 200, 220)))
            painter.drawText(QRectF(25, y, 100, 20),
                             Qt.AlignmentFlag.AlignLeft, label)
            painter.drawText(QRectF(195, y, 100, 20),
                             Qt.AlignmentFlag.AlignRight,
                             f"{value:.1f}%")

            # Bar background
            bar_x, bar_y, bar_w, bar_h = 25, y + 25, 270, 18
            painter.setPen(QPen(QColor(60, 60, 80), 1))
            painter.setBrush(QBrush(QColor(50, 50, 70)))
            painter.drawRoundedRect(QRectF(bar_x, bar_y, bar_w, bar_h), 9, 9)

            # Bar fill
            fill_w = bar_w * (value / 100.0)
            if fill_w > 0:
                t = value / 100.0
                fill_color = QColor(
                    int(color_low.red() + (color_high.red() - color_low.red()) * t),
                    int(color_low.green() + (color_high.green() - color_low.green()) * t),
                    int(color_low.blue() + (color_high.blue() - color_low.blue()) * t),
                )
                gradient = QRadialGradient(bar_x + fill_w / 2, bar_y, fill_w)
                gradient.setColorAt(0, fill_color.lighter(130))
                gradient.setColorAt(1, fill_color)
                painter.setPen(QPen(QColor(0, 0, 0, 0)))
                painter.setBrush(QBrush(gradient))
                painter.drawRoundedRect(
                    QRectF(bar_x, bar_y, fill_w, bar_h), 9, 9)

        # Network
        y_net = y_start + 3 * 65
        painter.setPen(QPen(QColor(200, 200, 220)))
        painter.drawText(QRectF(25, y_net, 150, 20),
                         Qt.AlignmentFlag.AlignLeft, "Network")

        net_str = self._format_bytes(self.slime.net_bytes)
        painter.setPen(QPen(QColor(255, 220, 100)))
        painter.drawText(QRectF(170, y_net, 125, 20),
                         Qt.AlignmentFlag.AlignRight, f"{net_str}/s")

        # Battery
        y_bat = y_net + 35
        painter.setPen(QPen(QColor(200, 200, 220)))
        painter.drawText(QRectF(25, y_bat, 150, 20),
                         Qt.AlignmentFlag.AlignLeft, "Battery")

        if self.slime.battery is not None:
            bat_color = QColor(100, 255, 100)
            if self.slime.battery < 20:
                bat_color = QColor(255, 80, 80)
            elif self.slime.battery < 50:
                bat_color = QColor(255, 200, 80)
            painter.setPen(QPen(bat_color))
            painter.drawText(QRectF(170, y_bat, 125, 20),
                             Qt.AlignmentFlag.AlignRight,
                             f"{self.slime.battery:.0f}%")
        else:
            painter.setPen(QPen(QColor(120, 120, 140)))
            painter.drawText(QRectF(170, y_bat, 125, 20),
                             Qt.AlignmentFlag.AlignRight, "AC Power")

        # Footer
        painter.setPen(QPen(QColor(100, 100, 130)))
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(QRectF(0, 385, 320, 20),
                         Qt.AlignmentFlag.AlignCenter,
                         "Desktop Pet Slime v1.0")

        painter.end()

    def _format_bytes(self, bps: float) -> str:
        if bps < 1024:
            return f"{bps:.0f} B"
        elif bps < 1024 * 1024:
            return f"{bps / 1024:.1f} KB"
        else:
            return f"{bps / (1024 * 1024):.1f} MB"
