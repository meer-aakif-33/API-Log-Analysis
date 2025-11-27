import time

import pytest

from function import analyze_api_logs


def test_invalid_types():
    logs = [
        {
            "timestamp": "2025-01-15T10:30:00Z",
            "endpoint": "/api/type",
            "method": "GET",
            "response_time_ms": "not-a-number",   # invalid
            "status_code": 200,
        }
    ]

    result = analyze_api_logs(logs)
    assert result["summary"]["total_requests"] == 0
    assert result["meta"]["invalid_logs"] == 1


def test_invalid_status_type():
    logs = [
        {
            "timestamp": "2025-01-15T10:30:00Z",
            "endpoint": "/api/type",
            "method": "GET",
            "response_time_ms": 10,
            "status_code": "200",  # invalid
        }
    ]
    result = analyze_api_logs(logs)
    assert result["summary"]["total_requests"] == 0
    assert result["meta"]["invalid_logs"] == 1


def test_performance_large_dataset():
    # 20,000 synthetic logs
    logs = []
    for i in range(20000):
        logs.append(
            {
                "timestamp": "2025-01-15T10:{:02d}:00Z".format(i % 60),
                "endpoint": "/api/endpoint/{}".format(i % 10),
                "method": "GET" if i % 2 == 0 else "POST",
                "response_time_ms": (i % 1000) + 1,
                "status_code": 200 if i % 20 != 0 else 500,
                "user_id": f"user_{i % 50}",
                "request_size_bytes": 500,
                "response_size_bytes": 2000,
            }
        )

    start = time.perf_counter()
    result = analyze_api_logs(logs)
    elapsed = time.perf_counter() - start

    assert result["summary"]["total_requests"] == 20000
    assert elapsed < 2.0  # under 2 seconds
