from function import analyze_api_logs

def run():
    import json
    with open("tests/test_data/sample_small.json") as f:
        logs = json.load(f)
    result = analyze_api_logs(logs)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    run()
