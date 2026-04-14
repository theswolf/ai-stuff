import json
import requests
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime


@dataclass
class AgentEvalResult:
    id: str
    message: str
    tool_sequence: list[str]
    expected_sequence: list[str]
    iterations: int
    sequence_match: bool
    under_max_iterations: bool
    passed: bool


def evaluate_agent(eval_dataset_path: str, service_url: str = "http://localhost:8000/agent/run", output_path: str = "eval/reports") -> dict:
    with open(eval_dataset_path) as f:
        dataset = json.load(f)
    results = []
    for item in dataset:
        resp = requests.post(service_url, json={"message": item["message"]})
        data = resp.json()
        tool_sequence = [c["tool"] for c in data.get("tool_calls", [])]
        expected = item.get("expected_tool_sequence", [])
        sequence_match = expected == tool_sequence[: len(expected)] if expected else True
        under_max = data.get("iterations", 0) <= item.get("max_iterations", 10)
        passed = sequence_match and under_max
        results.append(AgentEvalResult(item["id"], item["message"], tool_sequence, expected, data.get("iterations", 0), sequence_match, under_max, passed))
    passed_count = sum(1 for r in results if r.passed)
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_cases": len(results),
        "passed": passed_count,
        "failed": len(results) - passed_count,
        "pass_rate": round(passed_count / len(results), 3),
        "results": [asdict(r) for r in results],
    }
    Path(output_path).mkdir(parents=True, exist_ok=True)
    path = f"{output_path}/agent_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(path)
    return report


if __name__ == "__main__":
    evaluate_agent("eval/agent_eval_dataset.json")
