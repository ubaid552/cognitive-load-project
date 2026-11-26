"""
CogniLoad - System-Wide Keystroke Hook
Uses pynput to capture keystrokes from ALL applications
"""
import threading
import time
from datetime import datetime
from pynput import keyboard


class KeystrokeHook:
    def __init__(self, on_event_callback=None):
        self.events = []
        self.session_start = None
        self.last_key_time = None
        self.total_keystrokes = 0
        self.total_backspaces = 0
        self._listener = None
        self._running = False
        self._lock = threading.Lock()
        self.on_event_callback = on_event_callback

    def start(self):
        """Start monitoring keystrokes system-wide"""
        self.session_start = time.time() * 1000  # ms
        self._running = True
        self._listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=None,
            suppress=False  # Don't block keystrokes
        )
        self._listener.start()

    def stop(self):
        """Stop monitoring"""
        self._running = False
        if self._listener:
            self._listener.stop()

    def _on_key_press(self, key):
        if not self._running:
            return
        now = time.time() * 1000  # ms

        with self._lock:
            iki = (now - self.last_key_time) if self.last_key_time else None
            self.last_key_time = now

            is_bs = (key == keyboard.Key.backspace)
            is_del = (key == keyboard.Key.delete)
            is_revision = is_bs or is_del

            # Determine char info
            try:
                char = key.char
                ins_chars = 1 if char else 0
            except AttributeError:
                ins_chars = 0  # Special key

            del_chars = 1 if is_bs or is_del else 0

            event = {
                'type': 'deletion' if is_revision else ('insertion' if ins_chars > 0 else 'other'),
                'iki': iki,
                'duration': iki if iki else 100,
                'is_backspace': is_bs,
                'is_revision': is_revision,
                'ins_chars': ins_chars,
                'del_chars': del_chars,
                'del_words': 1 if del_chars > 4 else 0,
                'timestamp': now,
            }
            self.events.append(event)
            self.total_keystrokes += 1
            if is_bs:
                self.total_backspaces += 1

        # Fire callback
        if self.on_event_callback:
            try:
                self.on_event_callback(event, self.get_live_stats())
            except Exception:
                pass

    def get_events_snapshot(self) -> list:
        """Return a copy of current events"""
        with self._lock:
            return list(self.events)

    def get_live_stats(self) -> dict:
        """Get current live statistics"""
        with self._lock:
            elapsed_ms = (time.time() * 1000 - self.session_start) if self.session_start else 1
            ikis = [e['iki'] for e in self.events if e.get('iki')]
            avg_iki = sum(ikis) / len(ikis) if ikis else 0
            ins_chars = sum(e['ins_chars'] for e in self.events)
            words = max(1, ins_chars // 5)
            wpm = words / (elapsed_ms / 60000 + 0.001)
            long_pauses = sum(1 for i in ikis if i > 2000)
            return {
                'keystrokes': self.total_keystrokes,
                'backspaces': self.total_backspaces,
                'avg_iki_ms': round(avg_iki),
                'wpm': round(wpm),
                'long_pauses': long_pauses,
                'session_minutes': round(elapsed_ms / 60000, 1),
                'total_events': len(self.events),
            }

    def reset(self):
        """Reset session data"""
        with self._lock:
            self.events.clear()
            self.session_start = time.time() * 1000
            self.last_key_time = None
            self.total_keystrokes = 0
            self.total_backspaces = 0

    def get_total_time_ms(self) -> float:
        if self.session_start is None:
            return 60000
        return time.time() * 1000 - self.session_start
