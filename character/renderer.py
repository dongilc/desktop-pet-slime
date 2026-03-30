import math
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QPainterPath, QBrush, QPen, QColor,
    QRadialGradient, QLinearGradient, QCursor
)
from PyQt6.QtWidgets import QApplication

from character.slime import SlimeCharacter
from character.states import SlimeState


class SlimeRenderer:
    """Draws the slime character using QPainter."""

    def draw(self, painter: QPainter, slime: SlimeCharacter,
             widget_w: float, widget_h: float, widget_pos=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = widget_w / 2
        cy = widget_h / 2 + 10

        # Apply bounce
        cy += slime.bounce_offset

        # Scale
        s = slime.scale
        stretch = slime.stretch_factor

        # Get mouse position relative to widget for eye tracking
        mouse_dx, mouse_dy = 0.0, 0.0
        if widget_pos is not None:
            try:
                cursor = QCursor.pos()
                mouse_dx = (cursor.x() - widget_pos.x() - cx) / 200.0
                mouse_dy = (cursor.y() - widget_pos.y() - cy) / 200.0
                # Clamp
                mouse_dx = max(-1.0, min(1.0, mouse_dx))
                mouse_dy = max(-1.0, min(1.0, mouse_dy))
            except Exception:
                pass

        # Draw shadow
        self._draw_shadow(painter, cx, widget_h / 2 + 40, s)

        # Draw body
        self._draw_body(painter, cx, cy, s, stretch, slime)

        # Draw eyes (with mouse tracking)
        self._draw_eyes(painter, cx, cy - 15 * s * stretch, s, slime,
                        mouse_dx, mouse_dy)

        # Draw mouth
        self._draw_mouth(painter, cx, cy + 8 * s * stretch, s, slime)

        # Draw cheeks (blush when petted or happy)
        if slime.state in (SlimeState.PETTED, SlimeState.HAPPY):
            self._draw_cheeks(painter, cx, cy - 5 * s * stretch, s, slime)

        # Draw particles
        self._draw_particles(painter, slime)

        # Draw status indicator
        self._draw_status_icon(painter, cx, cy - 55 * s * stretch, slime)

    def _draw_shadow(self, painter: QPainter, cx, cy, scale):
        painter.save()
        painter.setOpacity(0.15)
        painter.setPen(QPen(QColor(0, 0, 0, 0)))
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        shadow_w = 55 * scale
        shadow_h = 12 * scale
        painter.drawEllipse(QPointF(cx, cy), shadow_w, shadow_h)
        painter.restore()

    def _draw_body(self, painter: QPainter, cx, cy, scale, stretch,
                   slime: SlimeCharacter):
        path = QPainterPath()
        w = 50 * scale
        h = 40 * scale * stretch
        j = slime.jiggle_offsets

        bx = cx - w
        by = cy + h * 0.3

        path.moveTo(bx, by)
        path.lineTo(cx + w, by)

        path.cubicTo(
            cx + w + 8 * scale + j[0], cy - h * 0.1 + j[1],
            cx + w * 0.6 + j[2], cy - h + j[3],
            cx + j[4], cy - h - 5 * scale + j[5]
        )

        path.cubicTo(
            cx - w * 0.6 + j[6], cy - h + j[7],
            cx - w - 8 * scale + j[8], cy - h * 0.1 + j[9],
            bx, by
        )

        path.closeSubpath()

        gradient = QRadialGradient(
            cx - 15 * scale, cy - 20 * scale, w * 1.8
        )
        base_color = slime.color
        gradient.setColorAt(0.0, base_color.lighter(160))
        gradient.setColorAt(0.4, base_color)
        gradient.setColorAt(1.0, base_color.darker(140))

        painter.setPen(QPen(base_color.darker(160), 2))
        painter.setBrush(QBrush(gradient))
        painter.drawPath(path)

        # Highlight shine
        self._draw_shine(painter, cx - 18 * scale, cy - 25 * scale, scale)

    def _draw_shine(self, painter: QPainter, x, y, scale):
        painter.save()
        painter.setOpacity(0.4)
        painter.setPen(QPen(QColor(0, 0, 0, 0)))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(QPointF(x, y), 8 * scale, 6 * scale)
        painter.setOpacity(0.25)
        painter.drawEllipse(QPointF(x + 12 * scale, y + 8 * scale),
                            4 * scale, 3 * scale)
        painter.restore()

    def _draw_cheeks(self, painter: QPainter, cx, cy, scale,
                     slime: SlimeCharacter):
        """Draw cute blush cheeks."""
        painter.save()
        opacity = 0.35
        if slime.state == SlimeState.PETTED:
            opacity = 0.55
        painter.setOpacity(opacity)
        painter.setPen(QPen(QColor(0, 0, 0, 0)))
        painter.setBrush(QBrush(QColor(255, 130, 150)))
        painter.drawEllipse(QPointF(cx - 28 * scale, cy), 8 * scale,
                            5 * scale)
        painter.drawEllipse(QPointF(cx + 28 * scale, cy), 8 * scale,
                            5 * scale)
        painter.restore()

    def _draw_eyes(self, painter: QPainter, cx, cy, scale,
                   slime: SlimeCharacter, mouse_dx=0.0, mouse_dy=0.0):
        eye_dist = 16 * scale
        eye_w = 7 * scale
        eye_h = 9 * scale * slime.eye_openness

        state = slime.state

        if state == SlimeState.HAPPY or state == SlimeState.PETTED:
            self._draw_happy_eyes(painter, cx, cy, eye_dist, scale)
        elif state == SlimeState.SLEEPY:
            eye_h *= 0.3
            self._draw_normal_eyes(painter, cx, cy, eye_dist, eye_w, eye_h,
                                   mouse_dx, mouse_dy, scale)
        elif state == SlimeState.SICK:
            self._draw_dizzy_eyes(painter, cx, cy, eye_dist, scale)
        elif state == SlimeState.STRESSED:
            eye_w *= 0.7
            eye_h *= 0.7
            self._draw_normal_eyes(painter, cx, cy, eye_dist, eye_w,
                                   max(eye_h, 1), mouse_dx, mouse_dy, scale)
        else:
            self._draw_normal_eyes(painter, cx, cy, eye_dist, eye_w,
                                   max(eye_h, 1), mouse_dx, mouse_dy, scale)

    def _draw_normal_eyes(self, painter, cx, cy, dist, w, h,
                          mouse_dx=0.0, mouse_dy=0.0, scale=1.0):
        # Eye tracking offset
        track_x = mouse_dx * 3 * scale
        track_y = mouse_dy * 2 * scale

        for side in [-1, 1]:
            ex = cx + side * dist
            # White of eye
            painter.setPen(QPen(QColor(0, 0, 0, 0)))
            painter.setBrush(QBrush(QColor(255, 255, 255, 60)))
            painter.drawEllipse(QPointF(ex, cy), w + 1, h + 1)

            # Pupil (follows mouse)
            painter.setBrush(QBrush(QColor(40, 40, 40)))
            painter.drawEllipse(QPointF(ex + track_x, cy + track_y), w, h)

            # Highlight
            if h > 3:
                painter.setBrush(QBrush(QColor(255, 255, 255)))
                painter.drawEllipse(
                    QPointF(ex + track_x - 2, cy + track_y - 2),
                    w * 0.35, h * 0.35
                )

    def _draw_happy_eyes(self, painter, cx, cy, dist, scale):
        painter.setPen(QPen(QColor(40, 40, 40), 2.5))
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))

        for side in [-1, 1]:
            ex = cx + side * dist
            path = QPainterPath()
            r = 6 * scale
            path.moveTo(ex - r, cy)
            path.cubicTo(ex - r, cy - r * 1.2,
                         ex + r, cy - r * 1.2,
                         ex + r, cy)
            painter.drawPath(path)

    def _draw_dizzy_eyes(self, painter, cx, cy, dist, scale):
        painter.setPen(QPen(QColor(40, 40, 40), 2))
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        r = 5 * scale

        for side in [-1, 1]:
            ex = cx + side * dist
            painter.drawLine(
                QPointF(ex - r, cy - r), QPointF(ex + r, cy + r))
            painter.drawLine(
                QPointF(ex + r, cy - r), QPointF(ex - r, cy + r))

    def _draw_mouth(self, painter: QPainter, cx, cy, scale,
                    slime: SlimeCharacter):
        state = slime.state
        painter.setPen(QPen(QColor(40, 40, 40), 2))
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))

        w = 10 * scale
        h = 6 * scale

        if state in (SlimeState.HAPPY, SlimeState.PETTED):
            path = QPainterPath()
            path.moveTo(cx - w, cy)
            path.cubicTo(cx - w * 0.5, cy + h * 1.5,
                         cx + w * 0.5, cy + h * 1.5,
                         cx + w, cy)
            painter.drawPath(path)
        elif state == SlimeState.STRESSED:
            path = QPainterPath()
            path.moveTo(cx - w, cy)
            path.cubicTo(cx - w * 0.3, cy - h * 0.5,
                         cx + w * 0.3, cy + h * 0.5,
                         cx + w, cy)
            painter.drawPath(path)
        elif state == SlimeState.SLEEPY:
            painter.drawEllipse(QPointF(cx, cy + 2), 4 * scale, 3 * scale)
        elif state == SlimeState.SICK:
            path = QPainterPath()
            path.moveTo(cx - w, cy)
            steps = 4
            for i in range(1, steps + 1):
                x = cx - w + (2 * w * i / steps)
                y = cy + (h * 0.8 if i % 2 else -h * 0.3)
                path.lineTo(x, y)
            painter.drawPath(path)
        elif state == SlimeState.HUNGRY:
            painter.setBrush(QBrush(QColor(80, 40, 40)))
            painter.drawEllipse(QPointF(cx, cy + 2), 7 * scale, 5 * scale)
        else:
            path = QPainterPath()
            path.moveTo(cx - w * 0.6, cy)
            path.cubicTo(cx - w * 0.2, cy + h * 0.8,
                         cx + w * 0.2, cy + h * 0.8,
                         cx + w * 0.6, cy)
            painter.drawPath(path)

    def _draw_particles(self, painter: QPainter, slime: SlimeCharacter):
        for p in slime.particles.particles:
            painter.save()
            painter.setOpacity(p.alpha * 0.8)
            color = QColor(255, 255, 100)
            painter.setPen(QPen(QColor(0, 0, 0, 0)))
            painter.setBrush(QBrush(color))
            self._draw_star(painter, p.x, p.y, p.size)
            painter.restore()

    def _draw_star(self, painter, x, y, size):
        path = QPainterPath()
        points = 4
        for i in range(points * 2):
            angle = math.pi * i / points - math.pi / 2
            r = size if i % 2 == 0 else size * 0.4
            px = x + r * math.cos(angle)
            py = y + r * math.sin(angle)
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)
        path.closeSubpath()
        painter.drawPath(path)

    def _draw_status_icon(self, painter: QPainter, cx, cy,
                          slime: SlimeCharacter):
        state = slime.state

        if state == SlimeState.SLEEPY:
            painter.setPen(QPen(QColor(100, 150, 255), 2))
            font = painter.font()
            font.setPointSize(12)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QPointF(cx + 10, cy - 5), "Z")
            font.setPointSize(9)
            painter.setFont(font)
            painter.drawText(QPointF(cx + 22, cy - 15), "z")

        elif state == SlimeState.HUNGRY:
            painter.setPen(QPen(QColor(255, 160, 50), 2))
            font = painter.font()
            font.setPointSize(14)
            painter.setFont(font)
            painter.drawText(QPointF(cx - 8, cy), "...")

        elif state == SlimeState.PETTED:
            self._draw_heart(painter, cx + 20, cy - 10, 6,
                             QColor(255, 100, 150))
            self._draw_heart(painter, cx - 15, cy - 5, 4,
                             QColor(255, 130, 170))
            self._draw_heart(painter, cx + 5, cy - 20, 3,
                             QColor(255, 160, 190))

        elif state == SlimeState.SICK:
            painter.setPen(QPen(QColor(0, 0, 0, 0)))
            painter.setBrush(QBrush(QColor(100, 180, 255, 180)))
            path = QPainterPath()
            path.moveTo(cx + 30, cy + 5)
            path.cubicTo(cx + 30, cy + 10, cx + 25, cy + 15, cx + 28, cy + 15)
            path.cubicTo(cx + 31, cy + 15, cx + 30, cy + 10, cx + 30, cy + 5)
            painter.drawPath(path)

        elif state == SlimeState.STRETCHING:
            painter.setPen(QPen(QColor(255, 230, 80), 2))
            font = painter.font()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QPointF(cx - 30, cy - 5), "Stretch~!")

    def _draw_heart(self, painter, x, y, size, color):
        painter.save()
        painter.setPen(QPen(QColor(0, 0, 0, 0)))
        painter.setBrush(QBrush(color))

        path = QPainterPath()
        path.moveTo(x, y + size * 0.4)
        path.cubicTo(x, y, x - size, y, x - size, y + size * 0.4)
        path.cubicTo(x - size, y + size * 0.8, x, y + size * 1.2,
                     x, y + size * 1.4)
        path.cubicTo(x, y + size * 1.2, x + size, y + size * 0.8,
                     x + size, y + size * 0.4)
        path.cubicTo(x + size, y, x, y, x, y + size * 0.4)
        painter.drawPath(path)
        painter.restore()
