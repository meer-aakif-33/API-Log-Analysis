"""
Main serverless-style entry point for API log analysis.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from config import (
    CACHING_MAX_CV,
    CACHING_MAX_ERROR_RATE,
    CACHING_MIN_GET_SHARE,
    CACHING_MIN_REQUESTS,
    DEFAULT_CACHE_TTL_MINUTES,
    EXECUTION_COST_PER_MS_USD,
    REQUEST_COST_USD,
)
from utils import (
    coefficient_of_variation,
    is_error_status,
    memory_cost_for_response_size,
    most_common_status,
    parse_timestamp,
    severity_from_error_rate,
    severity_from_response_time,
)


@dataclass
class EndpointAccumulator:
    count: int = 0
    sum_resp: float = 0.0
    sum_resp_sq: float = 0.0
    min_resp: Optional[float] = None
    max_resp: Optional[float] = None
    errors: int = 0
    status_counts: Counter = None
    method_counts: Counter = None

    def __post_init__(self) -> None:
        if self.status_counts is None:
            self.status_counts = Counter()
        if self.method_counts is None:
            self.method_counts = Counter()

    def update(
        self,
        response_time_ms: float,
        status_code: int,
        method: str,
        is_error: bool,
    ) -> None:
        self.count += 1
        self.sum_resp += response_time_ms
        self.sum_resp_sq += response_time_ms * response_time_ms
        self.status_counts[status_code] += 1
        self.method_counts[method.upper()] += 1

        if self.min_resp is None or response_time_ms < self.min_resp:
            self.min_resp = response_time_ms
        if self.max_resp is None or response_time_ms > self.max_resp:
            self.max_resp = response_time_ms
        if is_error:
            self.errors += 1


def analyze_api_logs(logs: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze API logs and return a comprehensive analytics report.

    Args:
        logs: Iterable of log dictionaries. Each item is expected to contain:
            - timestamp (str, ISO 8601)
            - endpoint (str)
            - method (str)
            - response_time_ms (int/float >= 0)
            - status_code (int)
            - user_id (str, optional)
            - request_size_bytes (int/float >= 0, optional)
            - response_size_bytes (int/float >= 0, optional)

    Returns:
        A nested dictionary matching (and extending) the expected JSON structure.

    Raises:
        TypeError: if logs is not an iterable of dict-like objects.
    """
    # Validate top-level type
    if not isinstance(logs, Iterable):
        raise TypeError("logs must be an iterable of dictionaries")

    total_requests = 0
    total_response_time = 0.0
    total_errors = 0
    earliest_ts: Optional[datetime] = None
    latest_ts: Optional[datetime] = None

    hourly_counts: Counter = Counter()
    user_counts: Counter = Counter()
    endpoint_acc: Dict[str, EndpointAccumulator] = {}

    # Cost tracking
    request_cost_total = 0.0
    execution_cost_total = 0.0
    memory_cost_total = 0.0
    endpoint_costs: Dict[str, float] = defaultdict(float)

    invalid_logs = 0

    for log in logs:
        if not isinstance(log, dict):
            invalid_logs += 1
            continue

        # Extract and validate fields
        try:
            timestamp_str = log["timestamp"]
            endpoint = log["endpoint"]
            method = log["method"]
            response_time_ms = log["response_time_ms"]
            status_code = log["status_code"]
        except KeyError:
            invalid_logs += 1
            continue

        user_id = log.get("user_id")
        request_size_bytes = log.get("request_size_bytes", 0)
        response_size_bytes = log.get("response_size_bytes", 0)

        # Basic type checks
        if not isinstance(timestamp_str, str) or not isinstance(endpoint, str) or not isinstance(method, str):
            invalid_logs += 1
            continue

        if not isinstance(response_time_ms, (int, float)) or not isinstance(status_code, int):
            invalid_logs += 1
            continue

        if not isinstance(request_size_bytes, (int, float)) or not isinstance(response_size_bytes, (int, float)):
            invalid_logs += 1
            continue

        if response_time_ms < 0 or request_size_bytes < 0 or response_size_bytes < 0:
            invalid_logs += 1
            continue

        # Parse timestamp
        dt = parse_timestamp(timestamp_str)
        if dt is None:
            invalid_logs += 1
            continue

        # ---- Valid log from here ----
        total_requests += 1
        total_response_time += float(response_time_ms)

        if earliest_ts is None or dt < earliest_ts:
            earliest_ts = dt
        if latest_ts is None or dt > latest_ts:
            latest_ts = dt

        hour_label = dt.strftime("%H:00")
        hourly_counts[hour_label] += 1

        if isinstance(user_id, str):
            user_counts[user_id] += 1

        error_flag = is_error_status(status_code)
        if error_flag:
            total_errors += 1

        # Endpoint accumulators
        acc = endpoint_acc.get(endpoint)
        if acc is None:
            acc = EndpointAccumulator()
            endpoint_acc[endpoint] = acc

        acc.update(
            response_time_ms=float(response_time_ms),
            status_code=status_code,
            method=method,
            is_error=error_flag,
        )

        # Cost accumulations
        request_cost = REQUEST_COST_USD
        execution_cost = float(response_time_ms) * EXECUTION_COST_PER_MS_USD
        memory_cost = memory_cost_for_response_size(float(response_size_bytes))

        request_cost_total += request_cost
        execution_cost_total += execution_cost
        memory_cost_total += memory_cost

        endpoint_costs[endpoint] += request_cost + execution_cost + memory_cost

    # ---- Build outputs ----

    # Summary
    if total_requests > 0:
        avg_response_time_ms = total_response_time / total_requests
        error_rate_pct = (total_errors / total_requests) * 100.0
    else:
        avg_response_time_ms = 0.0
        error_rate_pct = 0.0

    if earliest_ts is not None:
        start_str = earliest_ts.isoformat().replace("+00:00", "Z")
        end_str = latest_ts.isoformat().replace("+00:00", "Z")
        time_range = {"start": start_str, "end": end_str}
    else:
        time_range = None

    summary = {
        "total_requests": total_requests,
        "time_range": time_range,
        "avg_response_time_ms": avg_response_time_ms,
        "error_rate_percentage": error_rate_pct,
    }

    # Endpoint stats & performance issues
    endpoint_stats: List[Dict[str, Any]] = []
    performance_issues: List[Dict[str, Any]] = []

    for endpoint, acc in endpoint_acc.items():
        if acc.count > 0:
            ep_avg_resp = acc.sum_resp / acc.count
            ep_error_rate_pct = (acc.errors / acc.count) * 100.0 if acc.count > 0 else 0.0
        else:
            ep_avg_resp = 0.0
            ep_error_rate_pct = 0.0

        ep_stat = {
            "endpoint": endpoint,
            "request_count": acc.count,
            "avg_response_time_ms": ep_avg_resp,
            "slowest_request_ms": acc.max_resp,
            "fastest_request_ms": acc.min_resp,
            "error_count": acc.errors,
            "most_common_status": most_common_status(acc.status_counts),
        }
        endpoint_stats.append(ep_stat)

        # Performance issues: latency-based
        severity, threshold_ms = severity_from_response_time(ep_avg_resp)
        if severity is not None and threshold_ms is not None:
            performance_issues.append(
                {
                    "type": "slow_endpoint",
                    "endpoint": endpoint,
                    "avg_response_time_ms": ep_avg_resp,
                    "threshold_ms": threshold_ms,
                    "severity": severity,
                }
            )

        # Performance issues: error-rate-based
        err_sev = severity_from_error_rate(ep_error_rate_pct)
        if err_sev is not None:
            performance_issues.append(
                {
                    "type": "high_error_rate",
                    "endpoint": endpoint,
                    "error_rate_percentage": ep_error_rate_pct,
                    "severity": err_sev,
                }
            )

    # Sort endpoint stats for deterministic output (by endpoint name)
    endpoint_stats.sort(key=lambda e: e["endpoint"])

    # Hourly distribution (sorted by hour)
    hourly_distribution = {hour: hourly_counts[hour] for hour in sorted(hourly_counts.keys())}

    # Top users
    top_users_by_requests = [
        {"user_id": user_id, "request_count": count}
        for user_id, count in user_counts.most_common(5)
    ]

    # ---- Cost analysis (Option A) ----
    total_cost = request_cost_total + execution_cost_total + memory_cost_total

    cost_by_endpoint: List[Dict[str, Any]] = []
    for endpoint, total_ep_cost in endpoint_costs.items():
        ep_count = endpoint_acc[endpoint].count
        cost_by_endpoint.append(
            {
                "endpoint": endpoint,
                "total_cost": total_ep_cost,
                "cost_per_request": (total_ep_cost / ep_count) if ep_count > 0 else 0.0,
            }
        )

    cost_analysis = {
        "total_cost_usd": total_cost,
        "cost_breakdown": {
            "request_costs": request_cost_total,
            "execution_costs": execution_cost_total,
            "memory_costs": memory_cost_total,
        },
        "cost_by_endpoint": cost_by_endpoint,
        # Filled/adjusted after caching analysis:
        "optimization_potential_usd": 0.0,
    }

    # ---- Caching opportunities (Option D) ----
    caching_opportunities: List[Dict[str, Any]] = []
    total_requests_eliminated = 0
    total_cost_savings = 0.0
    total_performance_improvement_ms = 0.0

    for endpoint, acc in endpoint_acc.items():
        if acc.count < CACHING_MIN_REQUESTS:
            continue

        get_count = acc.method_counts.get("GET", 0)
        get_share = get_count / acc.count if acc.count > 0 else 0.0
        error_rate_pct = (acc.errors / acc.count) * 100.0 if acc.count > 0 else 0.0

        if get_share < CACHING_MIN_GET_SHARE:
            continue
        if error_rate_pct >= CACHING_MAX_ERROR_RATE:
            continue

        cv = coefficient_of_variation(acc.sum_resp, acc.sum_resp_sq, acc.count)
        if cv > CACHING_MAX_CV:
            # Too variable to confidently cache
            continue

        ep_avg_resp = acc.sum_resp / acc.count if acc.count > 0 else 0.0

        # Potential cache behavior (heuristic):
        potential_cache_hit_rate = int(round(get_share * 100))
        potential_requests_saved = int(round(acc.count * (potential_cache_hit_rate / 100.0)))

        ep_total_cost = endpoint_costs.get(endpoint, 0.0)
        ep_cost_per_request = ep_total_cost / acc.count if acc.count > 0 else 0.0
        estimated_cost_savings = potential_requests_saved * ep_cost_per_request

        caching_opportunities.append(
            {
                "endpoint": endpoint,
                "potential_cache_hit_rate": potential_cache_hit_rate,
                "current_requests": acc.count,
                "potential_requests_saved": potential_requests_saved,
                "estimated_cost_savings_usd": estimated_cost_savings,
                "recommended_ttl_minutes": DEFAULT_CACHE_TTL_MINUTES,
                "recommendation_confidence": "high" if cv < (CACHING_MAX_CV / 2) else "medium",
            }
        )

        total_requests_eliminated += potential_requests_saved
        total_cost_savings += estimated_cost_savings
        total_performance_improvement_ms += potential_requests_saved * ep_avg_resp

    caching_opportunities.sort(key=lambda c: c["estimated_cost_savings_usd"], reverse=True)

    caching_summary = {
        "caching_opportunities": caching_opportunities,
        "total_potential_savings": {
            "requests_eliminated": total_requests_eliminated,
            "cost_savings_usd": total_cost_savings,
            "performance_improvement_ms": total_performance_improvement_ms,
        },
    }

    # Now we can set optimization_potential_usd based on caching analysis
    cost_analysis["optimization_potential_usd"] = total_cost_savings

    # ---- Recommendations ----
    recommendations: List[str] = []

    # From caching opportunities
    for c in caching_opportunities:
        recommendations.append(
            f"Consider caching for {c['endpoint']} "
            f"({c['current_requests']} requests, {c['potential_cache_hit_rate']}% cache-hit potential)"
        )

    # From performance issues
    for issue in performance_issues:
        if issue["type"] == "slow_endpoint":
            recommendations.append(
                f"Investigate {issue['endpoint']} performance "
                f"(avg {issue['avg_response_time_ms']:.0f}ms exceeds {issue['threshold_ms']}ms threshold)"
            )
        elif issue["type"] == "high_error_rate":
            recommendations.append(
                f"Alert: {issue['endpoint']} has "
                f"{issue['error_rate_percentage']:.1f}% error rate"
            )

    result: Dict[str, Any] = {
        "summary": summary,
        "endpoint_stats": endpoint_stats,
        "performance_issues": performance_issues,
        "recommendations": recommendations,
        "hourly_distribution": hourly_distribution,
        "top_users_by_requests": top_users_by_requests,
        "cost_analysis": cost_analysis,
        "caching_opportunities": caching_summary["caching_opportunities"],
        "total_potential_savings": caching_summary["total_potential_savings"],
        "meta": {
            "invalid_logs": invalid_logs,
        },
    }

    return result
