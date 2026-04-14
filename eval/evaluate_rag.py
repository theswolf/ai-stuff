import json
import time
import statistics
import requests
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class EvalResult:
    question_id: str
    question: str
    answer: str
    latency_ms: float
    keyword_hit_rate: float
    contains_expected: bool
    passed: bool
    notes: str = ""


@dataclass
class EvalReport:
    timestamp: str
    total_questions: int
    passed: int
    failed: int
    pass_rate: float
    avg_latency_ms: float
    p95_latency_ms: float
    avg_keyword_hit_rate: float
    results: list[dict] = field(default_factory=list)


def evaluate_rag_system(eval_dataset_path: str, service_url: str = "http://localhost:8000", output_path: str = "eval/reports") -> EvalReport:
    with open(eval_dataset_path) as f:
        dataset = json.load(f)
    results = []
    latencies = []
    for item in dataset:
        start = time.time()
        response = requests.post(f"{service_url}/rag/query", json={"question": item["question"], "return_sources": False})
        latency_ms = (time.time() - start) * 1000
        latencies.append(latency_ms)
        answer = response.json().get("answer", "").lower()
        keywords = item.get("expected_keywords", [])
        if keywords:
            hits = sum(1 for kw in keywords if kw.lower() in answer)
            keyword_hit_rate = hits / len(keywords)
        else:
            keyword_hit_rate = 1.0
        expected = item.get("expected_answer_contains", "").lower()
        contains_expected = expected in answer if expected else True
        passed = keyword_hit_rate >= 0.5 and contains_expected
        results.append(EvalResult(item["id"], item["question"], answer[:200], round(latency_ms, 2), round(keyword_hit_rate, 3), contains_expected, passed))
    passed_count = sum(1 for r in results if r.passed)
    latencies_sorted = sorted(latencies)
    p95_index = max(0, int(len(latencies_sorted) * 0.95) - 1)
    report = EvalReport(
        timestamp=datetime.now().isoformat(),
        total_questions=len(dataset),
        passed=passed_count,
        failed=len(dataset) - passed_count,
        pass_rate=round(passed_count / len(dataset), 3),
        avg_latency_ms=round(statistics.mean(latencies), 2),
        p95_latency_ms=round(latencies_sorted[p95_index], 2),
        avg_keyword_hit_rate=round(statistics.mean(r.keyword_hit_rate for r in results), 3),
        results=[asdict(r) for r in results],
    )
    Path(output_path).mkdir(parents=True, exist_ok=True)
    report_path = f"{output_path}/rag_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w") as f:
        json.dump(asdict(report), f, indent=2, ensure_ascii=False)
    print(report_path)
    return report


if __name__ == "__main__":
    evaluate_rag_system("eval/rag_eval_dataset.json")
