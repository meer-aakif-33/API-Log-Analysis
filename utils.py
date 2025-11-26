"""
Utility helpers for API log analysis.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from math import sqrt
from typing import Any, Dict, Optional, Tuple

from config import (
    ERROR_RATE_CRITICAL_THRESHOLD,
    ERROR_RATE_HIGH_THRESHOLD,
    ERROR_RATE_MEDIUM_THRESHOLD,
    MEMORY_COST_LARGE_USD,
    MEMORY_COST_MEDIUM_USD,
    MEMORY_COST_SMALL_USD,
    MEDIUM_RESPONSE_BYTES,
    SMALL_RESPONSE_BYTES,
    SLOW_CRITICAL_THRESHOLD_MS,
    SLOW_HIGH_THRESHOLD_MS,
    SLOW_MEDIUM_THRESHOLD_MS,
)


def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Safely parse an ISO 8601 timestamp.

    Returns:
        A timezone-aware datetime in UTC, or None if invalid.
    """
    if not isinstance(timestamp_str, str):
        return None

    # Handle the common "Z" suffix for UTC
    if timestamp_str.endswith("Z"):
        timestamp_str = timestamp_str[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(timestamp_str)
    except ValueError:
        return None

    # Ensure UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return dt


def is_error_status(status_code: int) -> bool:
    """
    Decide whether a status code should be treated as an error.

    Here we treat 4xx and 5xx as errors.
    """
    if not isinstance(status_code, int):
        return False
    return 400 <= status_code <= 599


def severity_from_response_time(avg_ms: float) -> Tuple[Optional[str], Optional[int]]:
    """
    Map average response time to severity level and base threshold.

    Returns:
        (severity, threshold_ms) or (None, None) if no issue.
    """
    if avg_ms <= SLOW_MEDIUM_THRESHOLD_MS:
        return None, None
    if avg_ms <= SLOW_HIGH_THRESHOLD_MS:
        return "medium", SLOW_MEDIUM_THRESHOLD_MS
    if avg_ms <= SLOW_CRITICAL_THRESHOLD_MS:
        return "high", SLOW_MEDIUM_THRESHOLD_MS
    return "critical", SLOW_MEDIUM_THRESHOLD_MS


def severity_from_error_rate(rate_pct: float) -> Optional[str]:
    """
    Map error rate percentage to severity string.
    """
    if rate_pct <= ERROR_RATE_MEDIUM_THRESHOLD:
        return None
    if rate_pct <= ERROR_RATE_HIGH_THRESHOLD:
        return "medium"
    if rate_pct <= ERROR_RATE_CRITICAL_THRESHOLD:
        return "high"
    return "critical"


def memory_cost_for_response_size(bytes_size: float) -> float:
    """
    Compute memory cost from response size in bytes.
    """
    if bytes_size < 0:
        return 0.0
    if bytes_size <= SMALL_RESPONSE_BYTES:
        return MEMORY_COST_SMALL_USD
    if bytes_size <= MEDIUM_RESPONSE_BYTES:
        return MEMORY_COST_MEDIUM_USD
    return MEMORY_COST_LARGE_USD


def coefficient_of_variation(sum_x: float, sum_x2: float, n: int) -> float:
    """
    Compute coefficient of variation (std / mean) from aggregated stats.

    Returns 0.0 when not defined (e.g., n == 0 or mean == 0).
    """
    if n <= 0:
        return 0.0
    mean = sum_x / n
    if mean == 0:
        return 0.0
    variance = max((sum_x2 / n) - (mean ** 2), 0.0)
    std_dev = sqrt(variance)
    return std_dev / mean


def most_common_status(status_counts: Counter) -> Optional[int]:
    """
    Safely compute most common status code from a Counter.
    """
    if not status_counts:
        return None
    return status_counts.most_common(1)[0][0]
