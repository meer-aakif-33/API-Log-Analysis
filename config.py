"""
Configuration constants for API log analysis.
"""

# ---- Cost configuration ----
REQUEST_COST_USD = 0.0001
EXECUTION_COST_PER_MS_USD = 0.000002

MEMORY_COST_SMALL_USD = 0.00001   # 0–1 KB
MEMORY_COST_MEDIUM_USD = 0.00005  # 1–10 KB
MEMORY_COST_LARGE_USD = 0.0001    # 10 KB+

SMALL_RESPONSE_BYTES = 1024
MEDIUM_RESPONSE_BYTES = 10 * 1024

# ---- Performance thresholds (ms) ----
SLOW_MEDIUM_THRESHOLD_MS = 500
SLOW_HIGH_THRESHOLD_MS = 1000
SLOW_CRITICAL_THRESHOLD_MS = 2000

# ---- Error rate thresholds (%) ----
ERROR_RATE_MEDIUM_THRESHOLD = 5.0
ERROR_RATE_HIGH_THRESHOLD = 10.0
ERROR_RATE_CRITICAL_THRESHOLD = 15.0

# ---- Caching analysis configuration ----
CACHING_MIN_REQUESTS = 100
CACHING_MIN_GET_SHARE = 0.8   # >= 80% GET
CACHING_MAX_ERROR_RATE = 2.0  # < 2% error rate
CACHING_MAX_CV = 0.5          # Coefficient of variation for "consistent" latency
DEFAULT_CACHE_TTL_MINUTES = 15
