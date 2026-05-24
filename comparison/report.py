"""Generate comparison_report.md from outputs."""
from pathlib import Path

from shared.config import PROJECT_ROOT

OUTPUT_DIR = PROJECT_ROOT / "comparison" / "outputs"
REPORT_PATH = PROJECT_ROOT / "comparison" / "comparison_report.md"


def generate_report() -> str:
    """Build markdown report and write to comparison_report.md."""
    lines = [
        "# LocalMind Model Comparison Report",
        "",
        "Generated from local benchmark runs across 40 prompts (4 categories × 10).",
        "",
    ]

    if not OUTPUT_DIR.exists() or not list(OUTPUT_DIR.glob("*.json")):
        lines.append("_No comparison data yet. Run `python -m comparison.run_comparison` first._")
        REPORT_PATH.write_text("\n".join(lines))
        return "\n".join(lines)

    import json

    rows: list[tuple[str, float, float, float]] = []
    for path in sorted(OUTPUT_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        model = data.get("model", path.stem)
        rows.append(
            (
                model,
                data.get("avg_tokens_per_sec", 0),
                data.get("avg_latency_ms", 0),
                data.get("avg_memory_mb", 0),
            )
        )

    lines.extend(
        [
            "## Summary",
            "",
            "| Model | Avg t/s | Avg Latency (ms) | Avg Memory (MB) |",
            "|-------|---------|------------------|-----------------|",
        ]
    )
    for model, tps, lat, mem in rows:
        lines.append(f"| {model} | {tps} | {lat} | {mem} |")

    winner = max(rows, key=lambda r: r[1]) if rows else None
    if winner:
        lines.extend(
            [
                "",
                f"**Fastest throughput:** `{winner[0]}` at {winner[1]} tokens/sec",
                "",
            ]
        )

    lines.extend(
        [
            "## Category Notes",
            "",
            "- **Reasoning:** Logic puzzles and step-by-step deduction",
            "- **Coding:** Implementation and complexity questions",
            "- **Summarization:** Condensation and bullet summaries",
            "- **Creative:** Open-ended prose and wordplay",
            "",
            "## Recommendations",
            "",
        ]
    )

    if rows:
        fastest = max(rows, key=lambda r: r[1])
        lightest = min(rows, key=lambda r: r[3])
        lines.append(
            f"- Use **{fastest[0]}** when throughput matters most ({fastest[1]} t/s)."
        )
        lines.append(
            f"- Use **{lightest[0]}** when memory is constrained ({lightest[3]} MB avg)."
        )

    md = "\n".join(lines)
    REPORT_PATH.write_text(md)
    return md
