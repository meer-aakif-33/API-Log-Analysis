# import json
# from datetime import datetime, timedelta
# import random

# endpoints = ["/api/users", "/api/payments", "/api/reports", "/api/search", "/api/orders"]
# methods = ["GET", "POST"]
# status_codes = [200, 200, 200, 404, 500]  # Weighted 200

# logs = []
# ts = datetime(2025, 1, 15, 10, 0)

# for i in range(12000):
#     ts += timedelta(seconds=5)
#     logs.append({
#         "timestamp": ts.isoformat() + "Z",
#         "endpoint": random.choice(endpoints),
#         "method": random.choice(methods),
#         "response_time_ms": random.randint(50, 2500),
#         "status_code": random.choice(status_codes),
#         "user_id": f"user_{random.randint(1, 100)}",
#         "request_size_bytes": random.randint(200, 3000),
#         "response_size_bytes": random.randint(100, 20000)
#     })

# with open("sample_large.json", "w") as f:
#     json.dump(logs, f, indent=2)
import json
from datetime import datetime, timedelta
import random

endpoints = [
    "/api/users", "/api/payments", "/api/reports",
    "/api/search", "/api/orders", "/api/notifications"
]

methods = ["GET", "POST"]

# Weighted distribution to mimic real-world patterns
status_pool = [200] * 16 + [201] * 2 + [404] * 1 + [500] * 1

logs = []
ts = datetime(2025, 1, 15, 10, 0, 0)

for i in range(300):   # <-- 300 requests = medium dataset
    ts += timedelta(seconds=random.randint(2, 7))

    endpoint = random.choice(endpoints)
    method = random.choice(methods)

    response_time = random.randint(50, 2600)  # 50ms – 2600ms
    status = random.choice(status_pool)

    log = {
        "timestamp": ts.isoformat() + "Z",
        "endpoint": endpoint,
        "method": method,
        "response_time_ms": response_time,
        "status_code": status,
        "user_id": f"user_{random.randint(1, 60)}",
        "request_size_bytes": random.randint(200, 4096),
        "response_size_bytes": random.randint(100, 24000)
    }

    logs.append(log)

with open("sample_medium.json", "w") as f:
    json.dump(logs, f, indent=2)

print("sample_medium.json generated successfully! ✓")
