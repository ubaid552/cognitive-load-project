"""
CogniLoad - System Monitor
Tracks which application is currently active using psutil + Windows API
"""
import threading
import time

try:
    import psutil
    import ctypes
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


def get_active_app_name() -> str:
    """Get the name of the currently focused application"""
    if not PSUTIL_AVAILABLE:
        return "Unknown"
    try:
        import ctypes
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        pid = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        proc = psutil.Process(pid.value)
        return proc.name().replace('.exe', '')
    except Exception:
        return "Unknown"


class SystemMonitor:
    def __init__(self, update_interval: float = 2.0):
        self.update_interval = update_interval
        self._active_app = "Unknown"
        self._thread = None
        self._running = False
        self._lock = threading.Lock()
        self.app_time_map = {}  # {app_name: seconds_spent}
        self._last_app = None
        self._last_switch_time = time.time()

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _monitor_loop(self):
        while self._running:
            app = get_active_app_name()
            with self._lock:
                # Track time spent per app
                if self._last_app and self._last_app != app:
                    spent = time.time() - self._last_switch_time
                    self.app_time_map[self._last_app] = \
                        self.app_time_map.get(self._last_app, 0) + spent
                    self._last_switch_time = time.time()
                self._active_app = app
                if self._last_app != app:
                    self._last_app = app
            time.sleep(self.update_interval)

    def get_active_app(self) -> str:
        with self._lock:
            return self._active_app

    def get_app_summary(self) -> dict:
        with self._lock:
            return dict(self.app_time_map)

    def reset(self):
        with self._lock:
            self.app_time_map.clear()
            self._last_switch_time = time.time()
