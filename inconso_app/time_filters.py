from __future__ import annotations

from datetime import time

import pandas as pd

from .config import BUCKET_LABELS, HOUR_BUCKETS, SHIFT_WINDOWS


def assign_shift(value: time) -> str:
    """Return the production shift name matching a clock time."""
    for shift_name, (start, end) in SHIFT_WINDOWS.items():
        if shift_name == "Total":
            continue
        if start <= value <= end:
            return shift_name
    return "Poza zmianą"


def assign_bucket(value: time) -> str | pd.NA:
    """Return the configured hourly bucket label for a clock time."""
    for label, start, end in HOUR_BUCKETS:
        if start <= value < end or (label == HOUR_BUCKETS[-1][0] and value <= end):
            return label
    return pd.NA


def filter_by_time_window(df: pd.DataFrame, shift: str) -> pd.DataFrame:
    """Limit rows to the selected shift window."""
    if shift not in SHIFT_WINDOWS:
        return df
    start, end = SHIFT_WINDOWS[shift]
    return df[(df["Godzina"] >= start) & (df["Godzina"] <= end)].copy()


def bucket_range_labels(start_label: str, end_label: str) -> list[str]:
    """Return bucket labels between two selected bucket names."""
    start_index = BUCKET_LABELS.index(start_label)
    end_index = BUCKET_LABELS.index(end_label)
    if start_index > end_index:
        start_index, end_index = end_index, start_index
    return BUCKET_LABELS[start_index : end_index + 1]


def time_to_minutes(value: time) -> int:
    """Convert a clock time to minutes since midnight."""
    return value.hour * 60 + value.minute


def minutes_to_label(minutes: int) -> str:
    """Format minutes since midnight as HH:MM."""
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours:02d}:{mins:02d}"


def filter_by_clock_range(
    df: pd.DataFrame, start_time: time, end_time: time
) -> pd.DataFrame:
    """Limit rows to an exact clock range."""
    if start_time > end_time:
        start_time, end_time = end_time, start_time

    is_terminal_end = end_time == HOUR_BUCKETS[-1][2]
    if is_terminal_end:
        mask = (df["Godzina"] >= start_time) & (df["Godzina"] <= end_time)
    else:
        mask = (df["Godzina"] >= start_time) & (df["Godzina"] < end_time)
    return df[mask].copy()


def interval_label(value: time, interval_minutes: int) -> str:
    """Return the fixed-width interval label for a clock time."""
    start_minutes = time_to_minutes(value) // interval_minutes * interval_minutes
    end_minutes = start_minutes + interval_minutes
    return f"{minutes_to_label(start_minutes)}-{minutes_to_label(end_minutes)}"


def interval_labels_for_time_range(
    start_time: time, end_time: time, interval_minutes: int
) -> list[str]:
    """Return fixed-width interval labels overlapping the selected clock range."""
    start_minutes = time_to_minutes(start_time)
    end_minutes = time_to_minutes(end_time)
    if start_minutes > end_minutes:
        start_minutes, end_minutes = end_minutes, start_minutes

    first = start_minutes // interval_minutes * interval_minutes
    last = ((end_minutes + interval_minutes - 1) // interval_minutes) * interval_minutes
    labels = []
    for current in range(first, last, interval_minutes):
        if current + interval_minutes <= start_minutes or current >= end_minutes:
            continue
        labels.append(
            f"{minutes_to_label(current)}-{minutes_to_label(current + interval_minutes)}"
        )
    return labels


def bucket_labels_for_time_range(start_time: time, end_time: time) -> list[str]:
    """Return hourly buckets that overlap the selected clock range."""
    start_minutes = time_to_minutes(start_time)
    end_minutes = time_to_minutes(end_time)
    if start_minutes > end_minutes:
        start_minutes, end_minutes = end_minutes, start_minutes

    labels = []
    for label, bucket_start, bucket_end in HOUR_BUCKETS:
        bucket_start_minutes = time_to_minutes(bucket_start)
        bucket_end_minutes = time_to_minutes(bucket_end)
        if bucket_end_minutes > start_minutes and bucket_start_minutes < end_minutes:
            labels.append(label)
    return labels or BUCKET_LABELS
