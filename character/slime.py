from PyQt6.QtGui import QColor

from character.states import SlimeState, SlimeStateMachine, STATE_COLORS
from character.animations import (
    BounceAnimation, JiggleAnimation, BlinkAnimation,
    StretchAnimation, ParticleSystem
)


def lerp_color(c1: tuple, c2: tuple, t: float) -> QColor:
    t = max(0.0, min(1.0, t))
    return QColor(
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


class SlimeCharacter:
    """Central data model for the slime pet."""

    def __init__(self):
        # State
        self.state_machine = SlimeStateMachine()
        self._prev_state = SlimeState.IDLE
        self._color_transition = 1.0  # 0..1, 1 = fully transitioned
        self._prev_color = STATE_COLORS[SlimeState.IDLE]

        # System stats
        self.cpu = 0.0
        self.ram = 0.0
        self.disk = 0.0
        self.net_bytes = 0.0
        self.battery = None
        self.idle_seconds = 0.0

        # Animations
        self.bounce = BounceAnimation()
        self.jiggle = JiggleAnimation()
        self.blink = BlinkAnimation()
        self.stretch = StretchAnimation()
        self.particles = ParticleSystem()

        # Derived visual properties
        self.bounce_offset = 0.0
        self.jiggle_offsets = [0.0] * 10
        self.eye_openness = 1.0
        self.stretch_factor = 1.0
        self.color = QColor(120, 220, 120)
        self.scale = 1.0

    @property
    def state(self) -> SlimeState:
        return self.state_machine.state

    def pet(self):
        """Called when user clicks the slime."""
        self.state_machine.set_override(SlimeState.PETTED, 2.0)
        self.jiggle.trigger(15.0)

    def request_stretch(self):
        """Called for break reminder."""
        self.state_machine.set_override(SlimeState.STRETCHING, 5.0)
        self.stretch.trigger()

    def set_system_stats(self, cpu, ram, disk, net_bytes=0, battery=None,
                         idle_seconds=0):
        self.cpu = cpu
        self.ram = ram
        self.disk = disk
        self.net_bytes = net_bytes
        self.battery = battery
        self.idle_seconds = idle_seconds

        old_state = self.state_machine.state
        new_state = self.state_machine.evaluate(cpu, ram, disk, idle_seconds)

        if new_state != old_state:
            self._prev_color = (self.color.red(), self.color.green(),
                                self.color.blue())
            self._color_transition = 0.0
            self.jiggle.trigger(8.0)

        # Network particles
        self.particles.set_activity(net_bytes)

        # Scale based on RAM usage
        self.scale = 0.85 + 0.3 * (ram / 100.0)

    def tick(self, dt: float, center_x: float = 100, center_y: float = 100):
        """Advance all animations by dt seconds."""
        self.state_machine.tick(dt)

        # Animations
        self.bounce_offset = self.bounce.tick(dt)
        self.jiggle_offsets = self.jiggle.tick(dt)
        self.eye_openness = self.blink.tick(dt)
        self.stretch_factor = self.stretch.tick(dt)
        self.particles.tick(dt, center_x, center_y)

        # Color transition
        if self._color_transition < 1.0:
            self._color_transition = min(1.0, self._color_transition + dt * 2.0)

        target_color = STATE_COLORS[self.state]
        self.color = lerp_color(self._prev_color, target_color,
                                self._color_transition)
