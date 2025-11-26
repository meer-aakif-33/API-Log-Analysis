import json
from pathlib import Path

import pytest

from function import analyze_api_logs



def load_sample(name: str):
    base = Path(__file__).parent / "test_data"
    with open(base / name, "r", encoding="utf-8") as f:
        return json.load(f)


def test_basic_small_sample():
    logs = [
        {
            "timestamp": "2025-01-15T10:30:00Z",
            "endpoint": "/api/users",
            "method": "GET",
            "response_time_ms": 245,
            "status_code": 200,
            "user_id": "user_123",
            "request_size_bytes": 512,
            "response_size_bytes": 2048,
        },
        {
            "timestamp": "2025-01-15T10:31:15Z",
            "endpoint": "/api/payments",
            "method": "POST",
            "response_time_ms": 1450,
            "status_code": 500,
            "user_id": "user_456",
            "request_size_bytes": 1024,
            "response_size_bytes": 256,
        },
    ]

    result = analyze_api_logs(logs)

    assert result["summary"]["total_requests"] == 2
    assert result["summary"]["time_range"]["start"] == "2025-01-15T10:30:00+00:00".replace("+00:00", "Z")
    assert result["summary"]["time_range"]["end"] == "2025-01-15T10:31:15+00:00".replace("+00:00", "Z")

    # error rate: 1 out of 2
    assert pytest.approx(result["summary"]["error_rate_percentage"], rel=1e-6) == 50.0

    ep_users = next(e for e in result["endpoint_stats"] if e["endpoint"] == "/api/users")
    assert ep_users["request_count"] == 1
    assert ep_users["error_count"] == 0
    assert ep_users["most_common_status"] == 200

    ep_payments = next(e for e in result["endpoint_stats"] if e["endpoint"] == "/api/payments")
    assert ep_payments["request_count"] == 1
    assert ep_payments["error_count"] == 1
    assert ep_payments["most_common_status"] == 500

    # top users
    assert len(result["top_users_by_requests"]) == 2
    assert {u["user_id"] for u in result["top_users_by_requests"]} == {"user_123", "user_456"}


def test_empty_input():
    result = analyze_api_logs([])
    assert result["summary"]["total_requests"] == 0
    assert result["summary"]["avg_response_time_ms"] == 0.0
    assert result["summary"]["error_rate_percentage"] == 0.0
    assert result["summary"]["time_range"] is None
    assert result["endpoint_stats"] == []
    assert result["top_users_by_requests"] == []
    assert result["hourly_distribution"] == {}


def test_single_log():
    log = [
        {
            "timestamp": "2025-01-15T10:30:00Z",
            "endpoint": "/api/single",
            "method": "GET",
            "response_time_ms": 100,
            "status_code": 200,
            "user_id": "user_only",
        }
    ]

    result = analyze_api_logs(log)
    assert result["summary"]["total_requests"] == 1
    assert result["summary"]["time_range"]["start"].startswith("2025-01-15T10:30:00")
    assert len(result["endpoint_stats"]) == 1
    ep = result["endpoint_stats"][0]
    assert ep["endpoint"] == "/api/single"
    assert ep["request_count"] == 1
    assert ep["fastest_request_ms"] == 100
    assert ep["slowest_request_ms"] == 100


def test_malformed_and_invalid_skipped():
    logs = [
        {
            # missing endpoint
            "timestamp": "2025-01-15T10:30:00Z",
            "method": "GET",
            "response_time_ms": 100,
            "status_code": 200,
        },
        {
            # invalid timestamp
            "timestamp": "not-a-date",
            "endpoint": "/api/bad",
            "method": "GET",
            "response_time_ms": 100,
            "status_code": 200,
        },
        {
            # negative response time
            "timestamp": "2025-01-15T10:30:00Z",
            "endpoint": "/api/negative",
            "method": "GET",
            "response_time_ms": -10,
            "status_code": 200,
        },
        {
            # valid one
            "timestamp": "2025-01-15T10:31:00Z",
            "endpoint": "/api/good",
            "method": "GET",
            "response_time_ms": 120,
            "status_code": 200,
        },
    ]

    result = analyze_api_logs(logs)
    assert result["summary"]["total_requests"] == 1
    assert len(result["endpoint_stats"]) == 1
    assert result["endpoint_stats"][0]["endpoint"] == "/api/good"
    assert result["meta"]["invalid_logs"] == 3
