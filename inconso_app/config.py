from __future__ import annotations

from datetime import time
from pathlib import Path

APP_DIR = Path(__file__).parent
DEFAULT_CSV = APP_DIR / "Blocklist.csv"
ALL_LABEL = "Total"
FILTER_STATE_VERSION = "filters-total-default-v2"

SHIFT_WINDOWS = {
    "Total": (time(6, 7), time(22, 30)),
    "Shift 1": (time(6, 7), time(14, 15)),
    "Shift 2": (time(14, 20), time(22, 30)),
}

HOUR_BUCKETS = [
    ("6:00-7:00", time(6, 0), time(7, 0)),
    ("7:00-8:00", time(7, 0), time(8, 0)),
    ("8:00-9:00", time(8, 0), time(9, 0)),
    ("9:00-10:00", time(9, 0), time(10, 0)),
    ("10:00-11:00", time(10, 0), time(11, 0)),
    ("11:00-12:00", time(11, 0), time(12, 0)),
    ("12:00-13:00", time(12, 0), time(13, 0)),
    ("13:00-14:15", time(13, 0), time(14, 15)),
    ("14:20-15:00", time(14, 20), time(15, 0)),
    ("15:00-16:00", time(15, 0), time(16, 0)),
    ("16:00-17:00", time(16, 0), time(17, 0)),
    ("17:00-18:00", time(17, 0), time(18, 0)),
    ("18:00-19:00", time(18, 0), time(19, 0)),
    ("19:00-20:00", time(19, 0), time(20, 0)),
    ("20:00-21:00", time(20, 0), time(21, 0)),
    ("21:00-22:30", time(21, 0), time(22, 30)),
]
BUCKET_LABELS = [label for label, _, _ in HOUR_BUCKETS]
TIME_FILTER_START = time(6, 0)
TIME_FILTER_END = time(22, 30)

REQUIRED_COLUMNS = {
    "TimeTele",
    "Tray Sorter",
    "Tray Tray",
    "NokReason",
    "Station",
}

COLOR_SEQUENCE = [
    "#2563eb",
    "#dc2626",
    "#f59e0b",
    "#16a34a",
    "#7c3aed",
    "#0891b2",
    "#ea580c",
    "#64748b",
    "#be123c",
    "#0f766e",
]
