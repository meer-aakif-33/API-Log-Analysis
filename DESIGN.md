
# DESIGN.md — Rival.io API Log Analysis

## 🔍 Advanced Features Chosen & Rationale

I implemented the following two advanced features:

###  **Option A: Cost Estimation Engine**

I selected this feature because cost visibility is crucial for API consumers in serverless environments. Many engineering teams track performance but lack a clear view of *financial impact*. By attaching a cost model to each API call, the analytics become directly actionable for budgeting, optimization, and architectural decisions.
This feature turns raw API logs into **business-aligned insights**, which is highly valuable for engineering leadership and FinOps teams.

###  **Option D: Caching Opportunity Analysis**

Caching provides one of the highest ROI performance optimizations for API workloads. Identifying endpoints that are frequently called, error-free, and stable allows developers to offload unnecessary compute, reduce latency, and cut costs.
I selected this feature because it complements both performance analytics and cost estimation — showing not only *what is expensive or slow*, but also **what can be improved immediately with caching**.

---

##  Trade-offs and Design Decisions

| Design Area         | Decision                                                   | Trade-off                                                       |
| ------------------- | ---------------------------------------------------------- | --------------------------------------------------------------- |
| Processing strategy | Single-pass aggregation using dictionaries                 | More memory used per endpoint/user but O(n) time                |
| Timestamp parsing   | Parse on demand using `datetime`                           | Slight overhead per record but safer validation                 |
| Error handling      | Skip malformed logs & count them under `meta.invalid_logs` | Some logs ignored, but prevents pipeline failure                |
| Cost calculation    | Predefined constant cost model                             | Not customizable at runtime unless config modified              |
| Caching prediction  | Static heuristics (frequency > 100, 80% GET, etc.)         | Does not self-learn from trends but remains fully deterministic |

The guiding principle was **accuracy + performance first**, then **feature richness** without sacrificing runtime.

---

##  Scaling to 1 Million+ Logs

The current design is already optimized for large datasets (`O(n)` time, dictionary lookups).

To scale to **1M+ logs** or **real-time streaming**, the following enhancements are recommended:

### For Batch Processing

* Use `multiprocessing` to parallelize endpoint/user aggregations
* Replace CPython dictionaries with `PyPy` or `orjson` for faster JSON handling
* Stream JSON rather than loading full arrays (using `ijson`)

### For Real-Time Ingestion

* Convert logic into a pipeline supporting incremental aggregation
* Maintain rolling performance + cost metrics in Redis or DynamoDB
* Publish aggregated summaries to an event bus (Kafka / SNS)

### Memory Strategy

* Drop detailed per-request data after aggregation
* Compress partial aggregates to reduce memory footprint

With these improvements, the system can scale horizontally for **high-volume production workloads**.

---

## 🔧 What I Would Improve With More Time

If additional time were available, I would implement:

| Enhancement                               | Benefit                                |
| ----------------------------------------- | -------------------------------------- |
| UI dashboard to visualize trends          | More accessible analytics              |
| Support for anomaly detection (Feature B) | Security + operational insights        |
| Streaming mode for live API monitoring    | Near real-time feedback                |
| Pluggable cost model via config file      | Multi-cloud pricing support            |
| Persistent caching benefit tracker        | Time-series comparison of improvements |

These refinements would evolve the project from analytics into a **full observability platform**.

---

## ⏱ Time Spent

Approximately **7 hours total** including:

* Core implementation
* Advanced feature development
* Dataset preparation
* Test suite development
* Documentation

---

## 📌 Assumptions

To prevent ambiguity, I made the following reasonable assumptions:

* `status_code >= 400` counts as an error
* Missing or malformed fields invalidate a log entry rather than terminating execution
* Timestamps are expected in ISO-8601; invalid ones are skipped
* Cache potential is calculated based solely on observable patterns, no ML forecasting
