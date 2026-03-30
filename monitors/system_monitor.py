import psutil
from PyQt6.QtCore import QThread, pyqtSignal


class SystemMonitor(QThread):
    """Polls system stats and emits updates."""

    stats_updated = pyqtSignal(float, float, float, float, object)
    # cpu_percent, ram_percent, disk_percent, net_bytes_per_sec, battery_or_None

    def __init__(self, interval_ms=2000):
        super().__init__()
        self._interval = interval_ms / 1000.0
        self._running = True
        self._prev_net = None

    def run(self):
        while self._running:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('C:\\').percent

            # Network bytes/sec
            net = psutil.net_io_counters()
            net_total = net.bytes_sent + net.bytes_recv
            if self._prev_net is not None:
                net_bps = (net_total - self._prev_net) / self._interval
            else:
                net_bps = 0
            self._prev_net = net_total

            # Battery
            bat = psutil.sensors_battery()
            battery = bat.percent if bat else None

            self.stats_updated.emit(cpu, ram, disk, net_bps, battery)
            self.msleep(int(self._interval * 1000))

    def stop(self):
        self._running = False
        self.wait()
