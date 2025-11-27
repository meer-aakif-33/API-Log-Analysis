# Rival.io – API Log Analysis (Python)

This project implements a scalable analytics engine for processing API usage logs in a serverless environment.
The central function, `analyze_api_logs`, ingests raw API event data and generates detailed insights including performance metrics, error patterns, user behavior analysis, cost breakdowns, and caching optimization opportunities.

---

## Features

| Capability                                        | Status          |
| ------------------------------------------------- | --------------- |
| Total API request summary                         | Implemented     |
| Time range detection                              | Implemented     |
| Average response time                             | Implemented     |
| Global error rate                                 | Implemented     |
| Per-endpoint analytics                            | Implemented     |
| Performance issue detection                       | Implemented     |
| Actionable recommendations                        | Implemented     |
| Hourly request distribution                       | Implemented     |
| Top 5 active users                                | Implemented     |
| Advanced Feature A – Cost analysis                | Implemented     |
| Advanced Feature D – Caching opportunity analysis | Implemented     |
| Handling of malformed logs and edge cases         | Fully supported |

---

## Repository Structure

```
.
├── function.py                   # Core analytics logic
├── utils.py                      # Helper utilities
├── config.py                     # Thresholds and constants
├── main.py                       # CLI entrypoint
├── tests/
│   ├── test_function.py          # Core functionality tests
│   ├── test_edge_cases.py        # Edge case coverage
│   ├── test_integration_datasets.py
│   └── test_data/
│       ├── sample_small.json
│       ├── sample_medium.json
│       └── sample_large.json
├── README.md
├── DESIGN.md
├── requirements.txt
└── .gitignore
```

---

## Setup

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

---

## Running the Analyzer

```bash
python main.py
```

By default, the script loads `sample_small.json` and prints JSON-formatted analytics results.
The input file can be changed directly inside `main.py` or exposed as CLI arguments if extended.

---

## Testing

Run all tests:

```bash
pytest -q
```

Run tests with coverage:

```bash
pytest --cov=.
```

Expected output:

```
9 passed in ~1s
TOTAL COVERAGE: >80%
```
---
## Example Usage

Input (sample log record):
```json
[
  {
    "timestamp": "2025-01-15T10:30:00Z",
    "endpoint": "/api/users",
    "method": "GET",
    "response_time_ms": 245,
    "status_code": 200,
    "user_id": "user_123",
    "request_size_bytes": 512,
    "response_size_bytes": 2048
  }
]
````

Output (abridged):

```json
{
  "summary": {
    "total_requests": 1,
    "time_range": { ... },
    "avg_response_time_ms": 245.0,
    "error_rate_percentage": 0.0
  },
  "endpoint_stats": [...],
  "top_users_by_requests": [...],
  "cost_analysis": { ... },
  "caching_opportunities": [...]
}
```

---



## Performance Characteristics

* Processes 10,000 log entries in ≈0.07 seconds (verified benchmark)
* Single-pass O(n) aggregation over the dataset
* Core functionality has no heavy external dependencies
* Core functionality has no heavy external dependencies
* Space Complexity: O(e + u + h) — depends on number of unique endpoints(we store per-endpoint stats), number of users(for top users count), number of hours(for hourly distribution) respectivelyx

---

## Edge Case Coverage

| Scenario                      | Status    |
| ----------------------------- | --------- |
| Empty payload                 | Supported |
| Single event                  | Supported |
| Missing fields                | Supported |
| Invalid timestamps            | Supported |
| Negative values               | Supported |
| Non-dictionary items          | Supported |
| Case variance in HTTP methods | Supported |
| Large dataset (10k+ entries)  | Supported |

---

## Scalability Notes

* Stateless and functional architecture suitable for AWS Lambda / GCP Cloud Functions
* Can be adapted for streaming ingestion using a generator-based pipeline
* Can be extended to export metrics to Prometheus, CloudWatch, or similar observability systems

---

## Estimated Time Investment

Approximately 7 hours including design, implementation, testing, benchmarking, and documentation.

---

## Possible Future Enhancements

* Detection of rate-limiting violations
* Machine-learning-based anomaly detection on performance patterns
* Persisting analytics results to a datastore for dashboard consumption
* Web-based dashboard for interactive exploration of log insights

---
