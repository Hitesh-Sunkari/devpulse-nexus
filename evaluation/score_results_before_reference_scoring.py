import json
import re
import csv
from pathlib import Path
from collections import defaultdict

BASE = Path("evaluation")
RESULTS = BASE / "results.json"
RUBRIC = BASE / "rubric.json"
QUESTIONS = BASE / "questions.json"
REFERENCES = BASE / "reference_answers.json"
REFERENCE_ANSWERS = BASE / "reference_answers.json"

OUT_JSON = BASE / "week4_final_metrics.json"
OUT_DETAILS = BASE / "week4_question_scores.json"
OUT_CSV = BASE / "week4_category_report.csv"
OUT_MD = BASE / "week4_category_report.md"

results = json.loads(RESULTS.read_text(encoding="utf-8"))
rubric = json.loads(RUBRIC.read_text(encoding="utf-8"))
references = json.loads(REFERENCES.read_text(encoding="utf-8"))
reference_by_id = {x["id"]: x["reference_answer"] for x in references}
reference_answers = json.loads(REFERENCE_ANSWERS.read_text(encoding="utf-8"))
reference_by_id = {x["id"]: x for x in reference_answers}

rubric_by_id = {x["id"]: x for x in rubric}

# ------------------------------------------------------------
# Normalization
# ------------------------------------------------------------

def normalize(text):
    return re.sub(r"\s+", " ", str(text).lower()).strip()


def contains_concept(answer, concept):
    """
    Deterministic concept matching.

    Supports either:
      - a string
      - a list of alternative phrases
    """
    a = normalize(answer)

    if isinstance(concept, str):
        return normalize(concept) in a

    if isinstance(concept, list):
        return any(normalize(x) in a for x in concept)

    return False


def concept_score(answer, concepts):
    if not concepts:
        return 0.0

    hits = sum(
        contains_concept(answer, c)
        for c in concepts
    )

    return hits / len(concepts)


def required_pass(answer, concepts):
    if not concepts:
        return True

    return all(
        contains_concept(answer, c)
        for c in concepts
    )


def forbidden_hits(answer, forbidden):
    if not forbidden:
        return []

    a = normalize(answer)
    return [
        x for x in forbidden
        if normalize(x) in a
    ]


# ------------------------------------------------------------
# Build question-level scores
# ------------------------------------------------------------

question_scores = []

for r in results:

    rid = r["id"]
    rb = rubric_by_id[rid]

    answer = r.get("answer", "")
    reference_answer = reference_by_id[rid].get("reference_answer", "")
    expected = rb.get("expected_concepts", [])
    required = rb.get("required_concepts", [])
    forbidden = rb.get("hallucination_checks", [])

    coverage = concept_score(answer, expected)

    required_ok = required_pass(answer, required)

    forbidden_found = forbidden_hits(
        answer,
        forbidden
    )

    hallucination = bool(forbidden_found)

    # --------------------------------------------------------
    # Deterministic correctness
    # --------------------------------------------------------

    if hallucination:
        correctness = 0.0
    elif required_ok and coverage >= 0.75:
        correctness = 1.0
    elif coverage >= 0.35:
        correctness = 0.5
    else:
        correctness = 0.0

    # --------------------------------------------------------
    # Relevance
    #
    # Conservative proxy:
    # expected concepts present + answer length sanity.
    # This is not a human relevance judgment.
    # --------------------------------------------------------

    words = len(answer.split())

    if not answer.strip():
        relevance = 0.0
    elif coverage >= 0.75:
        relevance = 1.0
    elif coverage >= 0.35:
        relevance = 0.5
    else:
        relevance = 0.25

    # Penalize extremely generic/empty responses.
    if words < 8:
        relevance = min(relevance, 0.25)

    # --------------------------------------------------------
    # Code generation static quality
    #
    # We cannot honestly call code and execute it because the
    # original results did not capture generated-code separately.
    #
    # Therefore this is STATIC CODE QUALITY, not test-pass.
    # --------------------------------------------------------

    static_code_score = None

    if r["category"] == "Code Generation":

        code_markers = [
            "def ",
            "import ",
            "from ",
            "assert ",
            "return ",
            "app.",
            "@app.",
            "pytest",
        ]

        marker_hits = sum(
            m in answer.lower()
            for m in code_markers
        )

        if marker_hits >= 3 and coverage >= 0.50:
            static_code_score = 1.0
        elif marker_hits >= 1 and coverage >= 0.25:
            static_code_score = 0.5
        else:
            static_code_score = 0.0

    # --------------------------------------------------------
    # RAG grounding proxy
    #
    # Since retrieved chunks were NOT stored in results.json,
    # this measures answer grounding against expected KB
    # concepts. It is explicitly NOT retrieval precision.
    # --------------------------------------------------------

    rag_grounding = None

    if r["category"] == "RAG-based Question":
        rag_grounding = coverage

    question_scores.append({
        "id": rid,
        "category": r["category"],
        "model": r["model"],
        "correctness": correctness,
        "relevance": relevance,
        "concept_coverage": coverage,
        "hallucination": hallucination,
        "hallucination_terms": forbidden_found,
        "latency_seconds": r.get("latency_seconds"),
        "prompt_tokens": r.get("prompt_tokens"),
        "response_tokens": r.get("response_tokens"),
        "static_code_quality": static_code_score,
        "rag_grounding": rag_grounding,
        "answer": answer,
    })


# ------------------------------------------------------------
# Aggregation
# ------------------------------------------------------------

grouped = defaultdict(lambda: defaultdict(list))

for x in question_scores:
    grouped[x["category"]][x["model"]].append(x)


def avg(rows, key):
    vals = [
        x[key]
        for x in rows
        if x.get(key) is not None
    ]
    return sum(vals) / len(vals) if vals else None


def pct(value):
    return round(value * 100, 2) if value is not None else None


report = {
    "evaluation": {
        "total_records": len(results),
        "questions": 30,
        "models": sorted(set(x["model"] for x in results)),
        "categories": 7,
        "model_loading": "NONE",
        "scoring_type": "deterministic rubric/concept analysis",
    },
    "categories": {},
    "category_winners": {},
}


# ------------------------------------------------------------
# Category metrics
# ------------------------------------------------------------

for category, model_data in grouped.items():

    report["categories"][category] = {}

    for model, rows in model_data.items():

        total = len(rows)

        correct = sum(
            x["correctness"] == 1.0
            for x in rows
        )

        partial = sum(
            x["correctness"] == 0.5
            for x in rows
        )

        failed = sum(
            x["correctness"] == 0.0
            for x in rows
        )

        hallucinations = sum(
            x["hallucination"]
            for x in rows
        )

        latency = avg(rows, "latency_seconds")
        response_tokens = avg(rows, "response_tokens")
        prompt_tokens = avg(rows, "prompt_tokens")

        total_response_tokens = sum(
            x["response_tokens"]
            for x in rows
            if x["response_tokens"] is not None
        )

        # Throughput using measured total duration.
        original_rows = [
            r for r in results
            if r["model"] == model
            and r["category"] == category
        ]

        throughput = []

        for r in original_rows:
            t = r.get("response_tokens")
            d = r.get("total_duration_ns")

            if t and d and d > 0:
                throughput.append(
                    t / (d / 1_000_000_000)
                )

        data = {
            "tests": total,

            "correctness_percent":
                round(correct / total * 100, 2),

            "partial_percent":
                round(partial / total * 100, 2),

            "failure_percent":
                round(failed / total * 100, 2),

            "relevance_percent":
                pct(avg(rows, "relevance")),

            "concept_coverage_percent":
                pct(avg(rows, "concept_coverage")),

            "hallucination_rate_percent":
                round(hallucinations / total * 100, 2),

            "average_latency_seconds":
                round(latency, 2)
                if latency is not None else None,

            "average_prompt_tokens":
                round(prompt_tokens, 2)
                if prompt_tokens is not None else None,

            "average_response_tokens":
                round(response_tokens, 2)
                if response_tokens is not None else None,

            "total_response_tokens":
                total_response_tokens,

            "average_tokens_per_second":
                round(sum(throughput) / len(throughput), 2)
                if throughput else None,

            "test_pass_rate_percent": None,

            "static_code_quality_percent":
                None,

            "rag_grounding_percent":
                None,

            "retrieval_precision_percent":
                None,

            "retrieval_recall_percent":
                None,
        }

        # Code Generation:
        if category == "Code Generation":
            vals = [
                x["static_code_quality"]
                for x in rows
                if x["static_code_quality"] is not None
            ]

            if vals:
                data["static_code_quality_percent"] = round(
                    sum(vals) / len(vals) * 100,
                    2
                )

        # RAG:
        if category == "RAG-based Question":
            vals = [
                x["rag_grounding"]
                for x in rows
                if x["rag_grounding"] is not None
            ]

            if vals:
                data["rag_grounding_percent"] = round(
                    sum(vals) / len(vals) * 100,
                    2
                )

        report["categories"][category][model] = data


# ------------------------------------------------------------
# Category winners
# ------------------------------------------------------------

for category, model_data in report["categories"].items():

    ranking = []

    for model, d in model_data.items():

        ranking.append((
            model,
            d["correctness_percent"],
            d["concept_coverage_percent"] or 0,
            d["relevance_percent"] or 0,
            -(d["hallucination_rate_percent"] or 0),
            -(d["average_latency_seconds"] or 999999),
        ))

    ranking.sort(
        key=lambda x: x[1:],
        reverse=True
    )

    report["category_winners"][category] = {
        "winner": ranking[0][0],
        "ranking": [x[0] for x in ranking],
        "basis": [
            "correctness",
            "concept coverage",
            "relevance",
            "lower hallucination rate",
            "lower latency",
        ]
    }


# ------------------------------------------------------------
# Save JSON
# ------------------------------------------------------------

OUT_JSON.write_text(
    json.dumps(report, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

OUT_DETAILS.write_text(
    json.dumps(question_scores, indent=2, ensure_ascii=False),
    encoding="utf-8"
)


# ------------------------------------------------------------
# CSV
# ------------------------------------------------------------

with OUT_CSV.open(
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.writer(f)

    writer.writerow([
        "Category",
        "Model",
        "Correctness %",
        "Partial %",
        "Failure %",
        "Relevance %",
        "Concept Coverage %",
        "Hallucination %",
        "Latency sec",
        "Prompt Tokens Avg",
        "Response Tokens Avg",
        "Total Response Tokens",
        "Tokens/sec",
        "Static Code Quality %",
        "RAG Grounding %",
        "Test Pass Rate %",
        "Retrieval Precision %",
        "Retrieval Recall %",
    ])

    for category, models in report["categories"].items():

        for model, d in models.items():

            writer.writerow([
                category,
                model,
                d["correctness_percent"],
                d["partial_percent"],
                d["failure_percent"],
                d["relevance_percent"],
                d["concept_coverage_percent"],
                d["hallucination_rate_percent"],
                d["average_latency_seconds"],
                d["average_prompt_tokens"],
                d["average_response_tokens"],
                d["total_response_tokens"],
                d["average_tokens_per_second"],
                d["static_code_quality_percent"],
                d["rag_grounding_percent"],
                d["test_pass_rate_percent"],
                d["retrieval_precision_percent"],
                d["retrieval_recall_percent"],
            ])


# ------------------------------------------------------------
# Markdown report
# ------------------------------------------------------------

lines = []

lines.append("# DevPulse Nexus — Week 4 Category-wise Model Comparison")
lines.append("")
lines.append("## Evaluation Design")
lines.append("")
lines.append(
    "The same 30 questions were evaluated across all three models. "
    "The analysis is performed independently for the seven software-engineering "
    "task categories."
)
lines.append("")
lines.append(
    "**Models:** qwen2.5:1.5b, phi3:mini, tinyllama"
)
lines.append("")
lines.append(
    "**Model loading during scoring:** NONE"
)
lines.append("")

for category, models in report["categories"].items():

    lines.append(f"## {category}")
    lines.append("")
    lines.append(
        "| Model | Correctness | Partial | Failure | Relevance | "
        "Coverage | Hallucination | Latency | Tokens |"
    )
    lines.append(
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|"
    )

    for model, d in models.items():

        lines.append(
            f"| {model} | "
            f"{d['correctness_percent']}% | "
            f"{d['partial_percent']}% | "
            f"{d['failure_percent']}% | "
            f"{d['relevance_percent']}% | "
            f"{d['concept_coverage_percent']}% | "
            f"{d['hallucination_rate_percent']}% | "
            f"{d['average_latency_seconds']}s | "
            f"{d['total_response_tokens']} |"
        )

    winner = report["category_winners"][category]["winner"]

    lines.append("")
    lines.append(f"**Category winner: {winner}**")
    lines.append("")

    if category == "Code Generation":
        lines.append(
            "**Important:** true executable test-pass rate was not "
            "captured in the original results. Static code quality is "
            "reported separately and must not be called test-pass rate."
        )
        lines.append("")

    if category == "RAG-based Question":
        lines.append(
            "**Important:** retrieved chunks were not stored in the "
            "original results. RAG grounding is therefore reported as "
            "answer-to-reference alignment, not retrieval precision/recall."
        )
        lines.append("")


lines.append("## Final Category Winners")
lines.append("")
lines.append("| Category | Winner |")
lines.append("|---|---|")

for category, d in report["category_winners"].items():
    lines.append(
        f"| {category} | {d['winner']} |"
    )

lines.append("")
lines.append("## Interpretation")
lines.append("")
lines.append(
    "No single aggregate accuracy number is used as the primary conclusion. "
    "Model selection is based on category-specific software-engineering "
    "performance."
)
lines.append("")
lines.append(
    "Latency and token usage are treated as efficiency metrics rather than "
    "substitutes for correctness."
)
lines.append("")
lines.append(
    "Hallucination values are deterministic screening indicators based on "
    "forbidden/reference concepts; they are not equivalent to human-reviewed "
    "hallucination judgments."
)
lines.append("")
lines.append(
    "True code test-pass rate and retrieval precision/recall require "
    "additional instrumentation because those fields were not captured in "
    "the original 90 evaluation records."
)

OUT_MD.write_text(
    "\n".join(lines),
    encoding="utf-8"
)


# ------------------------------------------------------------
# Terminal report
# ------------------------------------------------------------

print()
print("=" * 100)
print("DEVPULSE NEXUS - WEEK 4 CATEGORY-WISE MODEL COMPARISON")
print("=" * 100)
print()
print("Evaluations :", len(results))
print("Questions   : 30")
print("Models      :", ", ".join(sorted(set(x["model"] for x in results))))
print("Categories  : 7")
print("Model load  : NONE")
print()

for category, models in report["categories"].items():

    print("=" * 100)
    print(category.upper())
    print("=" * 100)

    print(
        f"{'MODEL':<22}"
        f"{'CORRECT':>11}"
        f"{'PARTIAL':>11}"
        f"{'FAIL':>10}"
        f"{'RELEVANCE':>12}"
        f"{'COVERAGE':>12}"
        f"{'HALLUC.':>11}"
        f"{'LATENCY':>12}"
    )

    print("-" * 100)

    for model, d in models.items():

        print(
            f"{model:<22}"
            f"{d['correctness_percent']:>10.2f}%"
            f"{d['partial_percent']:>10.2f}%"
            f"{d['failure_percent']:>9.2f}%"
            f"{d['relevance_percent']:>11.2f}%"
            f"{d['concept_coverage_percent']:>11.2f}%"
            f"{d['hallucination_rate_percent']:>10.2f}%"
            f"{d['average_latency_seconds']:>10.2f}s"
        )

    winner = report["category_winners"][category]["winner"]

    print()
    print("CATEGORY WINNER:", winner)

    if category == "Code Generation":
        print(
            "Static code quality:",
            {
                m: d["static_code_quality_percent"]
                for m, d in models.items()
            }
        )
        print("Executable test-pass rate: NOT AVAILABLE")

    if category == "RAG-based Question":
        print(
            "RAG grounding:",
            {
                m: d["rag_grounding_percent"]
                for m, d in models.items()
            }
        )
        print("Retrieval precision/recall: NOT AVAILABLE")

    print()


print("=" * 100)
print("FINAL CATEGORY WINNERS")
print("=" * 100)

for category, d in report["category_winners"].items():
    print(
        f"{category:<32} -> {d['winner']}"
    )

print()
print("=" * 100)
print("FILES CREATED")
print("=" * 100)
print("Final metrics :", OUT_JSON)
print("Question data :", OUT_DETAILS)
print("CSV report    :", OUT_CSV)
print("Markdown      :", OUT_MD)
print("=" * 100)
