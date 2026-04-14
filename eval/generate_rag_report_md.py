import json
from pathlib import Path


def generate_markdown_report(json_report_path: str, output_path: str) -> None:
    with open(json_report_path) as f:
        report = json.load(f)
    md = f"""# Report di Valutazione RAG

**Data:** {report['timestamp']}

## Riepilogo

| Metrica | Valore |
|--------|--------|
| Domande totali | {report['total_questions']} |
| Pass rate | {report['pass_rate']:.1%} |
| Latency media | {report['avg_latency_ms']:.0f}ms |
| Latency p95 | {report['p95_latency_ms']:.0f}ms |
| Keyword hit rate | {report['avg_keyword_hit_rate']:.1%} |

## Risultati Dettagliati

| ID | Domanda | Pass | Latency | Keywords |
|----|---------|------|---------|----------|
"""
    for r in report["results"]:
        status = "✅" if r["passed"] else "❌"
        md += f"| {r['question_id']} | {r['question'][:50]}... | {status} | {r['latency_ms']:.0f}ms | {r['keyword_hit_rate']:.0%} |\n"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(md)


if __name__ == "__main__":
    generate_markdown_report("eval/reports/rag_eval_latest.json", "eval/reports/rag_eval_latest.md")
