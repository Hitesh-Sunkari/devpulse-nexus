import json
import re
import csv
from pathlib import Path
from collections import defaultdict
from statistics import mean, median

BASE = Path("evaluation")

RESULTS = BASE / "results.json"
RUBRIC = BASE / "rubric.json"

OUT_JSON = BASE / "week4_final_category_metrics.json"
OUT_CSV = BASE / "week4_final_category_report.csv"
OUT_MD = BASE / "week4_final_category_report.md"

results = json.loads(RESULTS.read_text(encoding="utf-8"))
rubric = json.loads(RUBRIC.read_text(encoding="utf-8"))

rubric_by_id = {x["id"]: x for x in rubric}

models = defaultdict(list)
categories = defaultdict(lambda: defaultdict(list))

for r in results:
    models[r["model"]].append(r)
    categories[r["category"]][r["model"]].append(r)


def normalize(text):
    return re.sub(r"\s+", " ", text.lower()).strip()


def concept_match(answer, concept):
    """
    Deterministic lexical concept check.
    No model is loaded.
    """
    a = normalize(answer)
    c = normalize(concept)

    if not c:
        return False

    # Direct phrase match
    if c in a:
        return True

    # Token overlap for multi-word concepts
    words = [w for w in re.findall(r"[a-z0-9_]+", c) if len(w) > 2]

    if not words:
        return False

    hits = sum(w in a for w in words)

    return hits / len(words) >= 0.75


def score_answer(r):
    qid = r["id"]
    rb = rubric_by_id[qid]

    answer = r.get("answer", "")

    expected = rb.get("expected_concepts", [])
    required = rb.get("required_concepts", [])
    forbidden = rb.get("hallucination_checks", [])

    expected_hits = sum(
        concept_match(answer, x)
        for x in expected
    )

    required_hits = sum(
        concept_match(answer, x)
        for x in required
    )

    coverage = (
        expected_hits / len(expected) * 100
        if expected else 0
    )

    required_coverage = (
        required_hits / len(required) * 100
        if required else 0
    )

    hallucinations = sum(
        concept_match(answer, x)
        for x in forbidden
    )

    hallucination = hallucinations > 0

    if required and required_hits == len(required):
        correctness = 1.0
    elif required and required_hits > 0:
        correctness = 0.5
    else:
        correctness = 0.0

    return {
        "correctness": correctness,
        "coverage": coverage,
        "required_coverage": required_coverage,
        "hallucination": hallucination,
        "hallucination_count": hallucinations,
    }


def percentile(values, p):
    if not values:
        return 0

    values = sorted(values)

    index = (len(values) - 1) * p
    lo = int(index)
    hi = min(lo + 1, len(values) - 1)

    if lo == hi:
        return values[lo]

    return values[lo] + (values[hi] - values[lo]) * (index - lo)


# ------------------------------------------------------------
# Score every answer
# ------------------------------------------------------------

scored = []

for r in results:
    s = score_answer(r)

    item = dict(r)
    item["evaluation"] = s

    scored.append(item)


# ------------------------------------------------------------
# Category/model metrics
# ------------------------------------------------------------

report = {
    "methodology": {
        "models_loaded_during_scoring": False,
        "evaluation_records": len(results),
        "questions": len(rubric),
        "categories": 7,
        "same_questions_for_all_models": True,
        "human_verified_accuracy": False,
        "hallucination_is_screening_signal": True,
        "code_execution_tests_available": False,
        "retrieval_logs_available": False,
    },
    "models": {},
    "categories": {},
}


for model, rows in models.items():

    sr = [
        x["evaluation"]
        for x in scored
        if x["model"] == model
    ]

    # Correctness
    correct = sum(x["correctness"] == 1.0 for x in sr)
    partial = sum(x["correctness"] == 0.5 for x in sr)
    failed = sum(x["correctness"] == 0.0 for x in sr)

    coverage = [x["coverage"] for x in sr]

    hallucinations = sum(
        x["hallucination"]
        for x in sr
    )

    latencies = [
        x["latency_seconds"]
        for x in rows
        if x.get("latency_seconds") is not None
    ]

    output_tokens = [
        x["response_tokens"]
        for x in rows
        if x.get("response_tokens") is not None
    ]

    throughput = []

    for x in rows:
        tok = x.get("response_tokens")
        duration = x.get("total_duration_ns")

        if tok and duration and duration > 0:
            throughput.append(
                tok / (duration / 1_000_000_000)
            )

    report["models"][model] = {
        "tests": len(rows),

        "execution": {
            "success_percent": round(
                sum(x.get("error") is None for x in rows)
                / len(rows) * 100,
                2
            )
        },

        "quality": {
            "correctness_percent": round(
                correct / len(sr) * 100, 2
            ),
            "partial_percent": round(
                partial / len(sr) * 100, 2
            ),
            "failure_percent": round(
                failed / len(sr) * 100, 2
            ),
            "concept_coverage_percent": round(
                mean(coverage), 2
            ) if coverage else 0,
            "hallucination_rate_percent": round(
                hallucinations / len(sr) * 100, 2
            ),
        },

        "performance": {
            "average_latency_seconds": round(
                mean(latencies), 2
            ) if latencies else 0,

            "median_latency_seconds": round(
                median(latencies), 2
            ) if latencies else 0,

            "p95_latency_seconds": round(
                percentile(latencies, 0.95), 2
            ) if latencies else 0,

            "average_output_tokens": round(
                mean(output_tokens), 2
            ) if output_tokens else 0,

            "total_output_tokens": sum(output_tokens),

            "average_tokens_per_second": round(
                mean(throughput), 2
            ) if throughput else 0,

            "median_tokens_per_second": round(
                median(throughput), 2
            ) if throughput else 0,
        }
    }


# ------------------------------------------------------------
# Category metrics
# ------------------------------------------------------------

for category, model_rows in categories.items():

    report["categories"][category] = {}

    for model, rows in model_rows.items():

        sr = [
            x["evaluation"]
            for x in scored
            if x["model"] == model
            and x["category"] == category
        ]

        n = len(sr)

        correct = sum(
            x["correctness"] == 1.0
            for x in sr
        )

        partial = sum(
            x["correctness"] == 0.5
            for x in sr
        )

        failed = sum(
            x["correctness"] == 0.0
            for x in sr
        )

        hallucinations = sum(
            x["hallucination"]
            for x in sr
        )

        coverages = [
            x["coverage"]
            for x in sr
        ]

        latencies = [
            x["latency_seconds"]
            for x in rows
            if x.get("latency_seconds") is not None
        ]

        data = {
            "tests": n,

            "correctness_percent": round(
                correct / n * 100, 2
            ),

            "partial_percent": round(
                partial / n * 100, 2
            ),

            "failure_percent": round(
                failed / n * 100, 2
            ),

            "relevance_percent": round(
                (correct + partial * 0.5) / n * 100,
                2
            ),

            "concept_coverage_percent": round(
                mean(coverages), 2
            ) if coverages else 0,

            "hallucination_rate_percent": round(
                hallucinations / n * 100,
                2
            ),

            "average_latency_seconds": round(
                mean(latencies), 2
            ) if latencies else 0,

            # These are intentionally NOT fabricated.
            "executable_test_pass_rate": None,
            "retrieval_precision_percent": None,
            "retrieval_recall_percent": None,
        }

        # Code generation
        if category == "Code Generation":
            data["code_execution_status"] = (
                "NOT AVAILABLE - generated code was not "
                "stored separately and executable tests "
                "were not run against model outputs."
            )

        # RAG
        if category == "RAG-based Question":
            data["retrieval_status"] = (
                "NOT AVAILABLE - retrieval documents/chunks "
                "were not stored in results.json."
            )

        report["categories"][category][model] = data


# ------------------------------------------------------------
# Winner selection
# ------------------------------------------------------------

# Primary comparison:
# correctness -> coverage -> latency
#
# This avoids declaring a winner based only on speed.

for category, model_data in report["categories"].items():

    ranking = []

    for model, d in model_data.items():

        ranking.append(
            (
                model,
                d["correctness_percent"],
                d["concept_coverage_percent"],
                -d["average_latency_seconds"],
            )
        )

    ranking.sort(
        key=lambda x: (x[1], x[2], x[3]),
        reverse=True
    )

    report["categories"][category]["winner"] = ranking[0][0]
    report["categories"][category]["ranking"] = [
        x[0] for x in ranking
    ]


# ------------------------------------------------------------
# Save JSON
# ------------------------------------------------------------

OUT_JSON.write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8"
)


# ------------------------------------------------------------
# CSV
# ------------------------------------------------------------

with OUT_CSV.open("w", newline="", encoding="utf-8") as f:

    writer = csv.writer(f)

    writer.writerow([
        "Category",
        "Model",
        "Tests",
        "Correctness %",
        "Partial %",
        "Failure %",
        "Relevance %",
        "Coverage %",
        "Hallucination %",
        "Latency sec",
        "P95 sec",
        "Output tokens",
        "Tokens/sec",
        "Code test pass %",
        "RAG precision %",
        "RAG recall %",
        "Winner",
    ])

    for category, model_data in report["categories"].items():

        winner = model_data["winner"]

        for model, d in model_data.items():

            if model in ("winner", "ranking"):
                continue

            perf = report["models"][model]["performance"]

            writer.writerow([
                category,
                model,
                d["tests"],
                d["correctness_percent"],
                d["partial_percent"],
                d["failure_percent"],
                d["relevance_percent"],
                d["concept_coverage_percent"],
                d["hallucination_rate_percent"],
                d["average_latency_seconds"],
                perf["p95_latency_seconds"],
                perf["total_output_tokens"],
                perf["average_tokens_per_second"],
                d["executable_test_pass_rate"],
                d["retrieval_precision_percent"],
                d["retrieval_recall_percent"],
                winner,
            ])


# ------------------------------------------------------------
# Markdown report
# ------------------------------------------------------------

lines = []

lines.append("# DevPulse Nexus - Week 4 Category-Wise Model Comparison")
lines.append("")
lines.append("## Evaluation design")
lines.append("")
lines.append(
    "- 30 identical evaluation questions were applied to all 3 models."
)
lines.append(
    "- 90 total model evaluations were analyzed."
)
lines.append(
    "- 7 software-engineering task categories were evaluated separately."
)
lines.append(
    "- Scoring was performed without loading any model."
)
lines.append(
    "- Correctness uses the predefined reference-concept rubric."
)
lines.append(
    "- Hallucination is a deterministic screening signal, not human proof."
)
lines.append("")

for category, model_data in report["categories"].items():

    lines.append(f"## {category}")
    lines.append("")
    lines.append(
        "| Model | Correctness | Partial | Failure | Relevance | "
        "Coverage | Hallucination | Latency |"
    )
    lines.append(
        "|---|---:|---:|---:|---:|---:|---:|---:|"
    )

    for model, d in model_data.items():

        if model in ("winner", "ranking"):
            continue

        lines.append(
            f"| {model} | "
            f"{d['correctness_percent']:.2f}% | "
            f"{d['partial_percent']:.2f}% | "
            f"{d['failure_percent']:.2f}% | "
            f"{d['relevance_percent']:.2f}% | "
            f"{d['concept_coverage_percent']:.2f}% | "
            f"{d['hallucination_rate_percent']:.2f}% | "
            f"{d['average_latency_seconds']:.2f}s |"
        )

    lines.append("")
    lines.append(
        f"**Category winner: {model_data['winner']}**"
    )
    lines.append("")

    if category == "Code Generation":
        lines.append(
            "**Executable test-pass rate:** Not available from "
            "the existing results because generated code was not "
            "stored/executed as test artifacts."
        )
        lines.append("")

    if category == "RAG-based Question":
        lines.append(
            "**Retrieval precision/recall:** Not available because "
            "retrieved documents/chunks were not stored in results.json."
        )
        lines.append("")

lines.append("## Final category winners")
lines.append("")

for category, data in report["categories"].items():
    lines.append(
        f"- **{category}:** {data['winner']}"
    )

lines.append("")
lines.append("## Important limitations")
lines.append("")
lines.append(
    "The existing 90 result records contain model answers, "
    "latency and token statistics, but do not contain retrieval "
    "documents/chunks or executable generated-code test results."
)
lines.append(
    "Therefore retrieval precision/recall and executable code "
    "test-pass rate are reported as unavailable rather than invented."
)

OUT_MD.write_text(
    "\n".join(lines),
    encoding="utf-8"
)


# ------------------------------------------------------------
# Terminal summary
# ------------------------------------------------------------

print()
print("=" * 100)
print("DEVPULSE NEXUS - FINAL CATEGORY-WISE EVALUATION")
print("=" * 100)

print(f"Questions       : {len(rubric)}")
print(f"Evaluations     : {len(results)}")
print("Models loaded   : NONE")
print("Categories      : 7")
print()

for category, model_data in report["categories"].items():

    print("=" * 100)
    print(category.upper())
    print("=" * 100)

    for model, d in model_data.items():

        if model in ("winner", "ranking"):
            continue

        print(
            f"{model:<22} "
            f"Correct={d['correctness_percent']:>6.2f}%  "
            f"Partial={d['partial_percent']:>6.2f}%  "
            f"Coverage={d['concept_coverage_percent']:>6.2f}%  "
            f"Halluc={d['hallucination_rate_percent']:>6.2f}%  "
            f"Latency={d['average_latency_seconds']:>7.2f}s"
        )

    print(
        f"\nCATEGORY WINNER: {model_data['winner']}"
    )

print()
print("=" * 100)
print("FINAL CATEGORY WINNERS")
print("=" * 100)

for category, data in report["categories"].items():
    print(f"{category:<32} -> {data['winner']}")

print()
print("=" * 100)
print("OUTPUT FILES")
print("=" * 100)
print(OUT_JSON)
print(OUT_CSV)
print(OUT_MD)
print("=" * 100)
print()
