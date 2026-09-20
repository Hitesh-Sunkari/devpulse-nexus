import json
from collections import defaultdict
from statistics import mean, median

RESULTS = "evaluation/results.json"
OUTPUT = "evaluation/week4_metrics.json"

with open(RESULTS, encoding="utf-8") as f:
    results = json.load(f)

models = defaultdict(list)
categories = defaultdict(lambda: defaultdict(list))

for r in results:
    model = r["model"]
    category = r["category"]

    models[model].append(r)
    categories[category][model].append(r)


def percentile(values, p):
    if not values:
        return None

    values = sorted(values)
    k = (len(values) - 1) * p
    lower = int(k)
    upper = min(lower + 1, len(values) - 1)

    if lower == upper:
        return values[lower]

    return values[lower] + (values[upper] - values[lower]) * (k - lower)


report = {
    "total_evaluations": len(results),
    "models": {}
}

for model, rows in models.items():

    latencies = [
        r["latency_seconds"]
        for r in rows
        if r.get("latency_seconds") is not None
    ]

    output_tokens = [
        r["response_tokens"]
        for r in rows
        if r.get("response_tokens") is not None
    ]

    throughput = []

    for r in rows:
        tokens = r.get("response_tokens")
        duration = r.get("total_duration_ns")

        if tokens and duration and duration > 0:
            throughput.append(
                tokens / (duration / 1_000_000_000)
            )

    errors = sum(r.get("error") is not None for r in rows)
    successful = len(rows) - errors

    report["models"][model] = {
        "evaluations": len(rows),
        "successful": successful,
        "execution_errors": errors,

        "success_rate_percent":
            round(successful / len(rows) * 100, 2),

        "error_rate_percent":
            round(errors / len(rows) * 100, 2),

        "latency": {
            "average_seconds":
                round(mean(latencies), 2) if latencies else None,

            "median_seconds":
                round(median(latencies), 2) if latencies else None,

            "p95_seconds":
                round(percentile(latencies, 0.95), 2)
                if latencies else None,

            "minimum_seconds":
                round(min(latencies), 2) if latencies else None,

            "maximum_seconds":
                round(max(latencies), 2) if latencies else None,
        },

        "output": {
            "total_tokens":
                sum(output_tokens) if output_tokens else 0,

            "average_tokens":
                round(mean(output_tokens), 2)
                if output_tokens else None,
        },

        "throughput": {
            "average_tokens_per_second":
                round(mean(throughput), 2)
                if throughput else None,

            "median_tokens_per_second":
                round(median(throughput), 2)
                if throughput else None,
        }
    }


# Category performance
report["categories"] = {}

for category, model_data in categories.items():

    report["categories"][category] = {}

    for model, rows in model_data.items():

        errors = sum(
            r.get("error") is not None
            for r in rows
        )

        report["categories"][category][model] = {
            "tests": len(rows),
            "successful": len(rows) - errors,
            "errors": errors,
            "pass_rate_execution_percent":
                round(
                    (len(rows) - errors) / len(rows) * 100,
                    2
                )
        }


with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print("=" * 72)
print("DEVPULSE NEXUS - WEEK 4 PERFORMANCE ANALYSIS")
print("=" * 72)

print(f"\nTotal evaluations: {len(results)}")

for model, data in report["models"].items():

    print(f"\nMODEL: {model}")
    print("-" * 72)

    print(f"Tests             : {data['evaluations']}")
    print(f"Successful        : {data['successful']}")
    print(f"Execution errors  : {data['execution_errors']}")
    print(f"Success rate      : {data['success_rate_percent']}%")

    l = data["latency"]

    print(f"Average latency   : {l['average_seconds']} sec")
    print(f"Median latency    : {l['median_seconds']} sec")
    print(f"P95 latency       : {l['p95_seconds']} sec")
    print(f"Min latency       : {l['minimum_seconds']} sec")
    print(f"Max latency       : {l['maximum_seconds']} sec")

    o = data["output"]

    print(f"Average output    : {o['average_tokens']} tokens")
    print(f"Total output      : {o['total_tokens']} tokens")

    t = data["throughput"]

    print(f"Average tok/sec   : {t['average_tokens_per_second']}")
    print(f"Median tok/sec    : {t['median_tokens_per_second']}")

print("\n" + "=" * 72)
print(f"Saved: {OUTPUT}")
print("=" * 72)
