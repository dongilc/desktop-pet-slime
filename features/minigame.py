import random
import math
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QRadialGradient, QPainterPath
)
from PyQt6.QtWidgets import QDialog


class FoodItem:
    FOOD_TYPES = [
        {"type": "apple", "color": (220, 50, 50), "points": 10},
        {"type": "candy", "color": (255, 150, 200), "points": 15},
        {"type": "star", "color": (255, 220, 50), "points": 25},
        {"type": "gem", "color": (100, 200, 255), "points": 30},
    ]

    # Bad items - lose points!
    BAD_TYPES = [
        {"type": "bomb", "color": (80, 80, 80), "points": -20},
    ]

    def __init__(self, game_width, difficulty: float = 0.0):
        # 15% chance of bad item, increases with difficulty
        if random.random() < 0.12 + difficulty * 0.08:
            food = random.choice(self.BAD_TYPES)
        else:
            food = random.choice(self.FOOD_TYPES)

        self.x = random.uniform(40, game_width - 40)
        self.y = -20.0
        self.speed = random.uniform(80, 140) + difficulty * 40
        self.size = random.uniform(14, 20)
        self.color = QColor(*food["color"])
        self.points = food["points"]
        self.type = food["type"]
        self.alive = True
        self.caught = False
        self.rotation = 0.0
        self.rot_speed = random.uniform(-200, 200)

    def tick(self, dt):
        self.y += self.speed * dt
        self.rotation += self.rot_speed * dt

    def hits_slime(self, slime_x, slime_y, slime_w):
        """Check if food overlaps with slime's catch area."""
        dx = abs(self.x - slime_x)
        dy = abs(self.y - slime_y)
        return dx < (slime_w + self.size) and dy < 30


class SlimeFeedGame(QDialog):
    """Mini-game: move the slime with mouse/keyboard to catch falling food!"""

    GAME_W = 400
    GAME_H = 500
    DURATION = 30  # seconds

    def __init__(self, slime, parent=None):
        super().__init__(parent)
        self.slime_ref = slime
        self.setWindowTitle("Feed the Slime!")
        self.setFixedSize(self.GAME_W, self.GAME_H)
        self.setCursor(Qt.CursorShape.BlankCursor)
        self.setMouseTracking(True)

        self.score = 0
        self.time_left = self.DURATION
        self.foods: list[FoodItem] = []
        self.combo = 0
        self.max_combo = 0
        self._spawn_timer = 0.0
        self._game_over = False
        self._started = False

        # Slime in game
        self._slime_x = self.GAME_W / 2
        self._slime_y = self.GAME_H - 65
        self._slime_w = 38.0  # half-width catch area
        self._slime_target_x = self._slime_x
        self._slime_happy = 0.0
        self._slime_hurt = 0.0
        self._slime_mouth_open = 0.0

        # Keyboard movement
        self._move_left = False
        self._move_right = False
        self._key_speed = 400.0  # pixels per second

        # Visual effects
        self._pops: list[dict] = []
        self._shake = 0.0
        self._bg_flash = 0.0

        # Ground particles
        self._ground_particles: list[dict] = []

        self._timer = QTimer(self)
        self._timer.setInterval(16)  # ~60 FPS for smooth movement
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        dt = 0.016

        if not self._started:
            self.update()
            return

        if self._game_over:
            self._shake *= 0.9
            self.update()
            return

        self.time_left -= dt

        if self.time_left <= 0:
            self.time_left = 0
            self._game_over = True
            self.update()
            return

        difficulty = 1.0 - (self.time_left / self.DURATION)  # 0.0 -> 1.0

        # Keyboard movement
        if self._move_left:
            self._slime_target_x -= self._key_speed * dt
        if self._move_right:
            self._slime_target_x += self._key_speed * dt

        # Clamp slime position
        margin = 35
        self._slime_target_x = max(margin,
                                    min(self.GAME_W - margin,
                                        self._slime_target_x))

        # Smooth follow
        lerp_speed = 12.0
        dx = self._slime_target_x - self._slime_x
        self._slime_x += dx * min(lerp_speed * dt, 1.0)

        # Spawn food
        self._spawn_timer += dt
        spawn_interval = max(0.35, 0.8 - difficulty * 0.45)
        if self._spawn_timer >= spawn_interval:
            self._spawn_timer = 0
            self.foods.append(FoodItem(self.GAME_W, difficulty))

        # Update food & check collisions
        for f in self.foods:
            if not f.alive:
                continue
            f.tick(dt)

            # Check if caught by slime
            if f.hits_slime(self._slime_x, self._slime_y, self._slime_w):
                f.alive = False
                f.caught = True

                if f.points > 0:
                    # Good food!
                    self.combo += 1
                    self.max_combo = max(self.max_combo, self.combo)
                    multiplier = 1.0 + (self.combo - 1) * 0.25
                    pts = int(f.points * multiplier)
                    self.score += pts
                    self._slime_happy = 1.0
                    self._slime_mouth_open = 1.0

                    self._pops.append({
                        "x": f.x, "y": f.y,
                        "text": f"+{pts}",
                        "color": f.color, "age": 0.0,
                    })

                    # Ground sparkle
                    for _ in range(5):
                        self._ground_particles.append({
                            "x": self._slime_x + random.uniform(-20, 20),
                            "y": self._slime_y + random.uniform(-10, 5),
                            "vx": random.uniform(-60, 60),
                            "vy": random.uniform(-80, -30),
                            "color": f.color, "age": 0.0,
                            "life": random.uniform(0.3, 0.6),
                            "size": random.uniform(2, 5),
                        })
                else:
                    # Bad food (bomb)!
                    self.combo = 0
                    self.score = max(0, self.score + f.points)
                    self._slime_hurt = 1.0
                    self._shake = 8.0
                    self._bg_flash = 1.0

                    self._pops.append({
                        "x": f.x, "y": f.y,
                        "text": f"{f.points}",
                        "color": QColor(255, 80, 80), "age": 0.0,
                    })

        # Remove off-screen food (missed)
        for f in self.foods:
            if f.alive and f.y > self.GAME_H + 30:
                f.alive = False
                if f.points > 0:
                    self.combo = 0  # miss resets combo

        self.foods = [f for f in self.foods if f.alive]

        # Update effects
        for p in self._pops:
            p["age"] += dt
        self._pops = [p for p in self._pops if p["age"] < 0.7]

        for gp in self._ground_particles:
            gp["age"] += dt
            gp["x"] += gp["vx"] * dt
            gp["y"] += gp["vy"] * dt
            gp["vy"] += 200 * dt  # gravity
        self._ground_particles = [
            gp for gp in self._ground_particles if gp["age"] < gp["life"]
        ]

        # Decay animations
        self._slime_happy *= 0.93
        self._slime_hurt *= 0.92
        self._slime_mouth_open *= 0.90
        self._shake *= 0.88
        self._bg_flash *= 0.90

        self.update()

    # --- Input ---

    def mouseMoveEvent(self, event):
        if not self._game_over:
            self._slime_target_x = event.position().x()

    def mousePressEvent(self, event):
        if not self._started:
            self._started = True
            return
        if self._game_over:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.close()

    def keyPressEvent(self, event):
        if not self._started:
            self._started = True
            return
        if event.key() == Qt.Key.Key_Left or event.key() == Qt.Key.Key_A:
            self._move_left = True
        elif event.key() == Qt.Key.Key_Right or event.key() == Qt.Key.Key_D:
            self._move_right = True
        elif event.key() == Qt.Key.Key_Escape:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.close()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key.Key_Left or event.key() == Qt.Key.Key_A:
            self._move_left = False
        elif event.key() == Qt.Key.Key_Right or event.key() == Qt.Key.Key_D:
            self._move_right = False

    # --- Drawing ---

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Screen shake
        if self._shake > 0.5:
            painter.translate(
                random.uniform(-self._shake, self._shake),
                random.uniform(-self._shake, self._shake)
            )

        # Background
        bg = QRadialGradient(self.GAME_W / 2, self.GAME_H / 2, self.GAME_W)
        bg.setColorAt(0, QColor(30, 30, 60))
        bg.setColorAt(1, QColor(15, 15, 35))
        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(QColor(0, 0, 0, 0)))
        painter.drawRect(-10, -10, self.GAME_W + 20, self.GAME_H + 20)

        # Red flash on bomb hit
        if self._bg_flash > 0.05:
            painter.setBrush(QBrush(QColor(255, 0, 0,
                                           int(self._bg_flash * 40))))
            painter.drawRect(-10, -10, self.GAME_W + 20, self.GAME_H + 20)

        # Ground line
        gy = self._slime_y + 28
        painter.setPen(QPen(QColor(60, 60, 100), 2))
        painter.drawLine(QPointF(0, gy), QPointF(self.GAME_W, gy))

        if not self._started:
            self._draw_start_screen(painter)
            painter.end()
            return

        if self._game_over:
            self._draw_game(painter)
            self._draw_game_over(painter)
        else:
            self._draw_game(painter)

        painter.end()

    def _draw_start_screen(self, painter: QPainter):
        # Draw slime in center
        self._draw_mini_slime(painter, self.GAME_W / 2, self.GAME_H / 2 + 30)

        painter.setPen(QPen(QColor(255, 255, 255)))
        font = painter.font()
        font.setPointSize(20)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            QRectF(0, 80, self.GAME_W, 40),
            Qt.AlignmentFlag.AlignCenter, "Feed the Slime!"
        )

        font.setPointSize(12)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QPen(QColor(180, 180, 220)))

        instructions = [
            "Move mouse or Arrow keys / A,D to move",
            "Catch food to score points!",
            "Avoid bombs!",
            "Combo = bonus multiplier",
        ]
        for i, text in enumerate(instructions):
            painter.drawText(
                QRectF(0, 150 + i * 28, self.GAME_W, 25),
                Qt.AlignmentFlag.AlignCenter, text
            )

        # Blink "click to start"
        painter.setPen(QPen(QColor(255, 220, 100)))
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            QRectF(0, self.GAME_H - 80, self.GAME_W, 30),
            Qt.AlignmentFlag.AlignCenter,
            "Click or press any key to start!"
        )

    def _draw_game(self, painter: QPainter):
        # Draw food items
        for f in self.foods:
            if not f.alive:
                continue
            painter.save()
            painter.translate(f.x, f.y)
            painter.rotate(f.rotation)

            if f.type == "bomb":
                self._draw_bomb(painter, f)
            elif f.type == "apple":
                self._draw_apple(painter, f)
            elif f.type == "candy":
                self._draw_candy(painter, f)
            elif f.type == "star":
                self._draw_star_food(painter, f)
            else:
                self._draw_gem(painter, f)

            painter.restore()

        # Ground particles
        for gp in self._ground_particles:
            painter.save()
            alpha = max(0, 1.0 - gp["age"] / gp["life"])
            c = QColor(gp["color"])
            c.setAlphaF(alpha)
            painter.setPen(QPen(QColor(0, 0, 0, 0)))
            painter.setBrush(QBrush(c))
            painter.drawEllipse(QPointF(gp["x"], gp["y"]),
                                gp["size"], gp["size"])
            painter.restore()

        # Draw slime
        self._draw_mini_slime(painter, self._slime_x, self._slime_y)

        # Pop effects
        for p in self._pops:
            painter.save()
            alpha = max(0, 1.0 - p["age"] / 0.7)
            color = QColor(p["color"])
            color.setAlphaF(alpha)
            painter.setPen(QPen(color, 2))
            font = painter.font()
            font.setPointSize(16)
            font.setBold(True)
            painter.setFont(font)
            y_offset = p["age"] * 60
            painter.drawText(QPointF(p["x"] - 20, p["y"] - y_offset),
                             p["text"])
            painter.restore()

        # HUD
        self._draw_hud(painter)

    def _draw_hud(self, painter: QPainter):
        # Semi-transparent HUD bar at top
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.setPen(QPen(QColor(0, 0, 0, 0)))
        painter.drawRect(0, 0, self.GAME_W, 45)

        painter.setPen(QPen(QColor(255, 255, 255)))
        font = painter.font()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)

        # Score
        painter.drawText(QRectF(15, 10, 150, 30),
                         Qt.AlignmentFlag.AlignLeft,
                         f"Score: {self.score}")

        # Timer
        time_color = QColor(255, 255, 255)
        if self.time_left < 10:
            time_color = QColor(255, 100, 100)
        painter.setPen(QPen(time_color))
        painter.drawText(QRectF(self.GAME_W - 120, 10, 110, 30),
                         Qt.AlignmentFlag.AlignRight,
                         f"Time: {int(self.time_left)}s")

        # Combo
        if self.combo > 1:
            painter.setPen(QPen(QColor(255, 200, 50)))
            font.setPointSize(13)
            painter.setFont(font)
            combo_text = f"x{self.combo} COMBO!"
            painter.drawText(
                QRectF(0, 10, self.GAME_W, 30),
                Qt.AlignmentFlag.AlignCenter, combo_text
            )

        # Time bar
        bar_y = 42
        bar_h = 3
        ratio = self.time_left / self.DURATION
        painter.setPen(QPen(QColor(0, 0, 0, 0)))
        painter.setBrush(QBrush(QColor(60, 60, 80)))
        painter.drawRect(QRectF(0, bar_y, self.GAME_W, bar_h))

        bar_color = QColor(100, 220, 100) if ratio > 0.3 else QColor(255, 80, 80)
        painter.setBrush(QBrush(bar_color))
        painter.drawRect(QRectF(0, bar_y, self.GAME_W * ratio, bar_h))

    def _draw_mini_slime(self, painter, cx, cy):
        # Shadow
        painter.save()
        painter.setOpacity(0.15)
        painter.setPen(QPen(QColor(0, 0, 0, 0)))
        painter.setBrush(QBrush(QColor(0, 0, 0)))
        painter.drawEllipse(QPointF(cx, cy + 25), 40, 8)
        painter.restore()

        # Body
        happy_scale = 1.0 + self._slime_happy * 0.12
        hurt_squish = 1.0 - self._slime_hurt * 0.1

        w = 38 * happy_scale * hurt_squish
        h = 28 * happy_scale

        # Hurt = red tint, otherwise use slime color
        if self._slime_hurt > 0.3:
            base_color = QColor(220, 80, 80)
        else:
            base_color = self.slime_ref.color

        gradient = QRadialGradient(cx - 8, cy - 12, w * 1.6)
        gradient.setColorAt(0.0, base_color.lighter(160))
        gradient.setColorAt(0.4, base_color)
        gradient.setColorAt(1.0, base_color.darker(140))

        # Body path (organic blob)
        path = QPainterPath()
        path.moveTo(cx - w, cy + h * 0.3)
        path.lineTo(cx + w, cy + h * 0.3)
        path.cubicTo(cx + w + 6, cy - h * 0.1,
                     cx + w * 0.6, cy - h,
                     cx, cy - h - 3)
        path.cubicTo(cx - w * 0.6, cy - h,
                     cx - w - 6, cy - h * 0.1,
                     cx - w, cy + h * 0.3)

        painter.setPen(QPen(base_color.darker(160), 2))
        painter.setBrush(QBrush(gradient))
        painter.drawPath(path)

        # Shine
        painter.save()
        painter.setOpacity(0.4)
        painter.setPen(QPen(QColor(0, 0, 0, 0)))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(QPointF(cx - 14, cy - 18), 7, 5)
        painter.restore()

        # Eyes
        ey = cy - 8
        if self._slime_hurt > 0.3:
            # X eyes when hurt
            painter.setPen(QPen(QColor(40, 40, 40), 2.5))
            for side in [-1, 1]:
                ex = cx + side * 12
                r = 5
                painter.drawLine(QPointF(ex - r, ey - r),
                                 QPointF(ex + r, ey + r))
                painter.drawLine(QPointF(ex + r, ey - r),
                                 QPointF(ex - r, ey + r))
        elif self._slime_happy > 0.3:
            # Happy ^_^ eyes
            painter.setPen(QPen(QColor(40, 40, 40), 2.5))
            painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
            for side in [-1, 1]:
                ex = cx + side * 12
                path = QPainterPath()
                path.moveTo(ex - 5, ey)
                path.cubicTo(ex - 5, ey - 7, ex + 5, ey - 7, ex + 5, ey)
                painter.drawPath(path)
        else:
            # Normal eyes
            painter.setPen(QPen(QColor(0, 0, 0, 0)))
            painter.setBrush(QBrush(QColor(40, 40, 40)))
            painter.drawEllipse(QPointF(cx - 12, ey), 5, 6)
            painter.drawEllipse(QPointF(cx + 12, ey), 5, 6)
            # Highlights
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(QPointF(cx - 13, ey - 2), 2, 2)
            painter.drawEllipse(QPointF(cx + 11, ey - 2), 2, 2)

        # Mouth
        my = cy + 5
        painter.setPen(QPen(QColor(40, 40, 40), 2))
        if self._slime_mouth_open > 0.3:
            # Open mouth eating!
            painter.setBrush(QBrush(QColor(80, 40, 40)))
            mouth_h = 6 * self._slime_mouth_open
            painter.drawEllipse(QPointF(cx, my + 2), 8, mouth_h)
        elif self._slime_hurt > 0.3:
            # Frowny wavy mouth
            painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
            path = QPainterPath()
            path.moveTo(cx - 8, my + 3)
            path.cubicTo(cx - 3, my - 2, cx + 3, my + 6, cx + 8, my + 1)
            painter.drawPath(path)
        else:
            # Neutral smile
            painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
            path = QPainterPath()
            path.moveTo(cx - 7, my)
            path.cubicTo(cx - 3, my + 5, cx + 3, my + 5, cx + 7, my)
            painter.drawPath(path)

    # --- Food drawing ---

    def _draw_bomb(self, painter, food):
        s = food.size
        # Body
        painter.setPen(QPen(QColor(40, 40, 40), 1.5))
        painter.setBrush(QBrush(QColor(60, 60, 60)))
        painter.drawEllipse(QPointF(0, 0), s, s)

        # Fuse
        painter.setPen(QPen(QColor(180, 140, 80), 2))
        path = QPainterPath()
        path.moveTo(0, -s)
        path.cubicTo(3, -s - 6, -3, -s - 10, 2, -s - 12)
        painter.drawPath(path)

        # Spark
        painter.setPen(QPen(QColor(255, 200, 50), 2))
        painter.setBrush(QBrush(QColor(255, 150, 30)))
        painter.drawEllipse(QPointF(2, -s - 12), 3, 3)

        # Skull mark
        painter.setPen(QPen(QColor(200, 200, 200), 1.5))
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
        painter.drawEllipse(QPointF(0, -2), s * 0.3, s * 0.3)
        # Cross bones hint
        r = s * 0.2
        painter.drawLine(QPointF(-r, 4), QPointF(r, 4))

    def _draw_apple(self, painter, food):
        painter.setPen(QPen(food.color.darker(130), 1.5))
        painter.setBrush(QBrush(food.color))
        painter.drawEllipse(QPointF(0, 0), food.size, food.size)
        # Stem
        painter.setPen(QPen(QColor(100, 70, 30), 2))
        painter.drawLine(QPointF(0, -food.size),
                         QPointF(2, -food.size - 5))
        # Leaf
        painter.setPen(QPen(QColor(0, 0, 0, 0)))
        painter.setBrush(QBrush(QColor(80, 180, 80)))
        painter.drawEllipse(QPointF(4, -food.size - 3), 5, 2.5)

    def _draw_candy(self, painter, food):
        painter.setPen(QPen(food.color.darker(130), 1.5))
        painter.setBrush(QBrush(food.color))
        painter.drawEllipse(QPointF(0, 0), food.size, food.size * 0.7)
        # Stripes
        painter.setPen(QPen(food.color.lighter(130), 1.5))
        painter.drawLine(QPointF(-food.size * 0.3, -food.size * 0.4),
                         QPointF(-food.size * 0.3, food.size * 0.4))
        painter.drawLine(QPointF(food.size * 0.3, -food.size * 0.4),
                         QPointF(food.size * 0.3, food.size * 0.4))
        # Wrapper ends
        painter.setPen(QPen(food.color.darker(110), 2))
        for sx in [-1, 1]:
            painter.drawLine(QPointF(sx * food.size, 0),
                             QPointF(sx * (food.size + 6), -4))
            painter.drawLine(QPointF(sx * food.size, 0),
                             QPointF(sx * (food.size + 6), 4))

    def _draw_star_food(self, painter, food):
        path = QPainterPath()
        for i in range(10):
            angle = math.pi * i / 5 - math.pi / 2
            r = food.size if i % 2 == 0 else food.size * 0.45
            px = r * math.cos(angle)
            py = r * math.sin(angle)
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)
        path.closeSubpath()

        gradient = QRadialGradient(0, 0, food.size)
        gradient.setColorAt(0, food.color.lighter(140))
        gradient.setColorAt(1, food.color)

        painter.setPen(QPen(food.color.darker(130), 1.5))
        painter.setBrush(QBrush(gradient))
        painter.drawPath(path)

    def _draw_gem(self, painter, food):
        s = food.size
        path = QPainterPath()
        path.moveTo(0, -s)
        path.lineTo(s * 0.8, -s * 0.3)
        path.lineTo(s * 0.5, s)
        path.lineTo(-s * 0.5, s)
        path.lineTo(-s * 0.8, -s * 0.3)
        path.closeSubpath()

        gradient = QRadialGradient(0, 0, s)
        gradient.setColorAt(0, food.color.lighter(150))
        gradient.setColorAt(1, food.color)

        painter.setPen(QPen(food.color.darker(130), 1.5))
        painter.setBrush(QBrush(gradient))
        painter.drawPath(path)

    def _draw_game_over(self, painter: QPainter):
        # Dark overlay
        painter.setBrush(QBrush(QColor(0, 0, 0, 160)))
        painter.setPen(QPen(QColor(0, 0, 0, 0)))
        painter.drawRect(-10, -10, self.GAME_W + 20, self.GAME_H + 20)

        font = painter.font()

        # Title
        painter.setPen(QPen(QColor(255, 255, 255)))
        font.setPointSize(28)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(
            QRectF(0, self.GAME_H / 2 - 100, self.GAME_W, 45),
            Qt.AlignmentFlag.AlignCenter, "Game Over!"
        )

        # Score
        painter.setPen(QPen(QColor(255, 220, 50)))
        font.setPointSize(22)
        painter.setFont(font)
        painter.drawText(
            QRectF(0, self.GAME_H / 2 - 45, self.GAME_W, 40),
            Qt.AlignmentFlag.AlignCenter, f"Score: {self.score}"
        )

        # Combo
        if self.max_combo > 1:
            painter.setPen(QPen(QColor(200, 200, 255)))
            font.setPointSize(15)
            painter.setFont(font)
            painter.drawText(
                QRectF(0, self.GAME_H / 2 + 5, self.GAME_W, 30),
                Qt.AlignmentFlag.AlignCenter,
                f"Best Combo: x{self.max_combo}"
            )

        # Rating
        rating = self._get_rating()
        painter.setPen(QPen(QColor(255, 180, 100)))
        font.setPointSize(16)
        painter.setFont(font)
        painter.drawText(
            QRectF(0, self.GAME_H / 2 + 40, self.GAME_W, 30),
            Qt.AlignmentFlag.AlignCenter, rating
        )

        # Close hint
        painter.setPen(QPen(QColor(150, 150, 150)))
        font.setPointSize(11)
        font.setBold(False)
        painter.setFont(font)
        painter.drawText(
            QRectF(0, self.GAME_H / 2 + 80, self.GAME_W, 25),
            Qt.AlignmentFlag.AlignCenter,
            "Click anywhere or press ESC to close"
        )

    def _get_rating(self) -> str:
        if self.score >= 500:
            return "Amazing! The slime is super happy!"
        elif self.score >= 300:
            return "Great job! The slime is full!"
        elif self.score >= 150:
            return "Not bad! The slime wants more~"
        elif self.score >= 50:
            return "Keep trying! The slime is still hungry..."
        else:
            return "The slime is starving..."
