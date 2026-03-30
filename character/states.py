from enum import Enum, auto


class SlimeState(Enum):
    IDLE = auto()
    HAPPY = auto()
    STRESSED = auto()
    SLEEPY = auto()
    HUNGRY = auto()
    SICK = auto()
    PETTED = auto()
    STRETCHING = auto()


# State -> (R, G, B) color mapping
STATE_COLORS = {
    SlimeState.IDLE: (120, 220, 120),      # 연두
    SlimeState.HAPPY: (0, 200, 100),        # 초록
    SlimeState.STRESSED: (220, 50, 50),     # 빨강
    SlimeState.SLEEPY: (100, 150, 255),     # 파랑
    SlimeState.HUNGRY: (255, 160, 50),      # 주황
    SlimeState.SICK: (180, 100, 220),       # 보라
    SlimeState.PETTED: (255, 150, 200),     # 분홍
    SlimeState.STRETCHING: (255, 230, 80),  # 노랑
}


class SlimeStateMachine:
    """Determines slime state based on system stats."""

    def __init__(self):
        self.state = SlimeState.IDLE
        self._override_state = None
        self._override_timer = 0.0

    def set_override(self, state: SlimeState, duration: float):
        self._override_state = state
        self._override_timer = duration

    def tick(self, dt: float):
        if self._override_timer > 0:
            self._override_timer -= dt
            if self._override_timer <= 0:
                self._override_state = None

    def evaluate(self, cpu: float, ram: float, disk: float,
                 idle_seconds: float = 0) -> SlimeState:
        if self._override_state:
            self.state = self._override_state
            return self.state

        # Priority-based state selection
        if disk > 90:
            new_state = SlimeState.SICK
        elif cpu > 80:
            new_state = SlimeState.STRESSED
        elif ram > 85:
            new_state = SlimeState.HUNGRY
        elif idle_seconds > 300:  # 5 minutes
            new_state = SlimeState.SLEEPY
        elif cpu < 30:
            new_state = SlimeState.HAPPY
        else:
            new_state = SlimeState.IDLE

        self.state = new_state
        return self.state
