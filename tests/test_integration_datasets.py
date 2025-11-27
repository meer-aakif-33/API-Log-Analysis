import json
from function import analyze_api_logs

def test_medium_json_loads():
    with open("tests/test_data/sample_medium.json") as f: #300 requests in sample_medium.json 
        logs = json.load(f)
    result = analyze_api_logs(logs)
    assert result["summary"]["total_requests"] > 0

def test_large_json_loads():
    with open("tests/test_data/sample_large.json") as f: #12000 requests in sample_large.json
        logs = json.load(f)
    result = analyze_api_logs(logs)
    assert result["summary"]["total_requests"] > 0
