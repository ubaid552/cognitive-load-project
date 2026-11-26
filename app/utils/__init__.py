"""
CogniLoad — Utils Package
Shared utility helpers used across the application.
"""
import os
import json
from datetime import datetime


def get_project_root() -> str:
    """Return the absolute path to the cogniload_app/ root directory."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def format_timestamp(iso_str: str, fmt: str = "%Y-%m-%d  %H:%M") -> str:
    """Format an ISO datetime string for display."""
    try:
        dt = datetime.fromisoformat(iso_str[:19])
        return dt.strftime(fmt)
    except Exception:
        return iso_str[:16] if iso_str else "—"


def safe_json_loads(text: str, default=None):
    """Parse JSON safely, returning default on failure."""
    try:
        return json.loads(text)
    except Exception:
        return default if default is not None else {}


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp value between lo and hi."""
    return max(lo, min(hi, value))


def ms_to_readable(ms: float) -> str:
    """Convert milliseconds to a human-readable string."""
    if ms < 1000:
        return f"{int(ms)} ms"
    elif ms < 60000:
        return f"{ms/1000:.1f} s"
    else:
        return f"{ms/60000:.1f} min"


__all__ = [
    "get_project_root",
    "format_timestamp",
    "safe_json_loads",
    "clamp",
    "ms_to_readable",
]
