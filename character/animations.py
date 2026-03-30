import math
import random


class BounceAnimation:
    """Continuous sinusoidal vertical bounce."""

    def __init__(self, amplitude=8.0, frequency=0.5):
        self.amplitude = amplitude
        self.frequency = frequency
        self._phase = 0.0

    def tick(self, dt: float) -> float:
        self._phase += dt * self.frequency * 2 * math.pi
        return math.sin(self._phase) * self.amplitude


class JiggleAnimation:
    """Decaying jiggle triggered by events."""

    def __init__(self, num_points=10):
        self.num_points = num_points
        self._amplitude = 0.0
        self._phase = 0.0
        self._decay = 5.0

    def trigger(self, amplitude=12.0):
        self._amplitude = amplitude
        self._phase = 0.0

    def tick(self, dt: float) -> list[float]:
        if self._amplitude < 0.1:
            return [0.0] * self.num_points

        self._phase += dt * 15.0
        self._amplitude *= math.exp(-self._decay * dt)

        return [
            math.sin(self._phase + i * 0.7) * self._amplitude
            for i in range(self.num_points)
        ]


class BlinkAnimation:
    """Periodic random blink."""

    def __init__(self):
        self._openness = 1.0
        self._timer = random.uniform(2.0, 5.0)
        self._blinking = False
        self._blink_phase = 0.0

    def tick(self, dt: float) -> float:
        if self._blinking:
            self._blink_phase += dt
            if self._blink_phase < 0.07:
                self._openness = max(0.0, 1.0 - self._blink_phase / 0.07)
            elif self._blink_phase < 0.15:
                self._openness = 0.0
            elif self._blink_phase < 0.22:
                self._openness = min(1.0, (self._blink_phase - 0.15) / 0.07)
            else:
                self._openness = 1.0
                self._blinking = False
                self._timer = random.uniform(2.0, 5.0)
        else:
            self._timer -= dt
            if self._timer <= 0:
                self._blinking = True
                self._blink_phase = 0.0

        return self._openness


class StretchAnimation:
    """Stretch animation for break reminders."""

    def __init__(self):
        self._active = False
        self._phase = 0.0
        self._duration = 5.0

    @property
    def active(self):
        return self._active

    def trigger(self):
        self._active = True
        self._phase = 0.0

    def tick(self, dt: float) -> float:
        """Returns vertical stretch factor (1.0 = normal)."""
        if not self._active:
            return 1.0

        self._phase += dt
        if self._phase >= self._duration:
            self._active = False
            return 1.0

        t = self._phase / self._duration
        return 1.0 + 0.3 * math.sin(t * math.pi * 2)


class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-30, 30)
        self.vy = random.uniform(-50, -20)
        self.alpha = 1.0
        self.lifetime = random.uniform(0.5, 1.5)
        self.age = 0.0
        self.size = random.uniform(2, 5)

    def tick(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.alpha = max(0, 1.0 - self.age / self.lifetime)
        return self.age < self.lifetime


class ParticleSystem:
    """Sparkle particles for network activity."""

    def __init__(self):
        self.particles: list[Particle] = []
        self._spawn_timer = 0.0

    def set_activity(self, bytes_per_sec: float):
        # More network activity = more particles
        self._spawn_rate = min(bytes_per_sec / 50000, 10.0)

    def tick(self, dt: float, center_x: float, center_y: float):
        # Spawn new particles
        if self._spawn_rate > 0:
            self._spawn_timer += dt
            interval = 1.0 / max(self._spawn_rate, 0.1)
            while self._spawn_timer >= interval:
                self._spawn_timer -= interval
                self.particles.append(Particle(
                    center_x + random.uniform(-30, 30),
                    center_y + random.uniform(-20, 10)
                ))

        # Update existing
        self.particles = [p for p in self.particles if p.tick(dt)]

    @property
    def _spawn_rate(self):
        return getattr(self, '_rate', 0.0)

    @_spawn_rate.setter
    def _spawn_rate(self, val):
        self._rate = val
