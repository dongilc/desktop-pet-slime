import ctypes
import ctypes.wintypes
from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]


def get_idle_seconds() -> float:
    lii = LASTINPUTINFO()
    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
    millis = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
    return millis / 1000.0


class ActivityMonitor(QObject):
    """Monitors user idle time and emits break reminders."""

    break_needed = pyqtSignal()
    idle_updated = pyqtSignal(float)  # idle seconds

    def __init__(self, break_interval_min=45, parent=None):
        super().__init__(parent)
        self.break_interval = break_interval_min * 60  # seconds
        self._continuous_active = 0.0
        self._last_idle = 0.0
        self._break_sent = False

        self._timer = QTimer(self)
        self._timer.setInterval(10000)  # check every 10s
        self._timer.timeout.connect(self._check)
        self._timer.start()

    def _check(self):
        idle = get_idle_seconds()
        self.idle_updated.emit(idle)

        if idle < 30:
            # User is active
            self._continuous_active += 10
            if (self._continuous_active >= self.break_interval
                    and not self._break_sent):
                self.break_needed.emit()
                self._break_sent = True
        else:
            # User stepped away - reset
            self._continuous_active = 0
            self._break_sent = False

        self._last_idle = idle
