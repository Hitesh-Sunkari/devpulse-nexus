import json
import time
import requests
from pathlib import Path

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

# Smallest/safest models first.
MODELS = [
    "qwen2.5:1.5b",
    "tinyllama",
    "phi3:mini",
]

QUESTIONS_FILE = Path("evaluation/questions.json")
OUTPUT_FILE = Path("evaluation/results.json")

# Conservative settings for a 7.3 GiB RAM VM
NUM_CTX = 2048
NUM_PREDICT = 80
TIMEOUT = 90
KEEP_ALIVE = "5m"


def load_json(path):
    if not path.exists():
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_results(results):
    # Atomic save: prevents corrupted results if Ubuntu freezes/crashes.
    temp = OUTPUT_FILE.with_suffix(".tmp")

    with open(temp, "w", encoding="utf-8") as f:
        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False,
        )

    temp.replace(OUTPUT_FILE)


def completed_keys(results):
    # Only successful evaluations are considered complete.
    return {
        (x.get("model"), x.get("id"))
        for x in results
        if x.get("error") is None
    }


def remove_old_failed_result(results, model, qid):
    return [
        x for x in results
        if not (
            x.get("model") == model
            and x.get("id") == qid
            and x.get("error") is not None
        )
    ]


def unload_model(model):
    try:
        requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": "",
                "keep_alive": 0,
            },
            timeout=10,
        )
        print(f"  Unloaded {model}", flush=True)
    except Exception:
        pass


def ask_model(model, question):
    prompt = (
        "Answer the following software-engineering question accurately "
        "and concisely. Do not invent information. "
        "Use only information supported by the DevPulse Nexus codebase "
        "and Docker knowledge referenced by the question.\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )

    start = time.perf_counter()

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": KEEP_ALIVE,
            "options": {
                "num_ctx": NUM_CTX,
                "num_predict": NUM_PREDICT,
                "temperature": 0,
            },
        },
        timeout=TIMEOUT,
    )

    response.raise_for_status()

    elapsed = round(time.perf_counter() - start, 3)
    data = response.json()

    return {
        "answer": data.get("response", "").strip(),
        "latency_seconds": elapsed,
        "prompt_tokens": data.get("prompt_eval_count"),
        "response_tokens": data.get("eval_count"),
        "total_duration_ns": data.get("total_duration"),
    }


def main():
    questions = load_json(QUESTIONS_FILE)

    if not questions:
        print("ERROR: evaluation/questions.json is empty or missing.")
        return

    results = load_json(OUTPUT_FILE)

    # Remove duplicate records, preserving the newest record.
    unique = {}

    for item in results:
        key = (item.get("model"), item.get("id"))
        unique[key] = item

    results = list(unique.values())

    completed = completed_keys(results)

    total = len(questions) * len(MODELS)

    print("=" * 60)
    print("DevPulse Nexus - Efficient Evaluation")
    print("=" * 60)
    print(f"Questions : {len(questions)}")
    print(f"Models    : {len(MODELS)}")
    print(f"Total     : {total}")
    print(f"Completed : {len(completed)}")
    print(f"Remaining : {total - len(completed)}")
    print("=" * 60)

    # ONE MODEL AT A TIME.
    for model in MODELS:

        remaining = [
            q for q in questions
            if (model, q["id"]) not in completed
        ]

        if not remaining:
            print(f"\n{model}: already complete. Skipping.")
            continue

        print()
        print("=" * 60)
        print(f"MODEL: {model}")
        print(f"Remaining: {len(remaining)}")
        print("=" * 60)

        ok_count = 0
        error_count = 0

        for index, item in enumerate(remaining, 1):

            qid = item["id"]

            print(
                f"[{index}/{len(remaining)}] "
                f"{model} - Q{qid}",
                flush=True,
            )

            try:
                output = ask_model(
                    model,
                    item["question"],
                )

                result = {
                    "id": qid,
                    "category": item["category"],
                    "question": item["question"],
                    "model": model,
                    **output,
                    "error": None,
                }

                ok_count += 1

                print(
                    f"  OK | "
                    f"{output['latency_seconds']}s | "
                    f"{output['response_tokens']} tokens",
                    flush=True,
                )

            except Exception as exc:

                result = {
                    "id": qid,
                    "category": item["category"],
                    "question": item["question"],
                    "model": model,
                    "answer": "",
                    "latency_seconds": None,
                    "prompt_tokens": None,
                    "response_tokens": None,
                    "total_duration_ns": None,
                    "error": str(exc),
                }

                error_count += 1

                print(
                    f"  ERROR | {exc}",
                    flush=True,
                )

            # Remove previous failed attempt for this exact question/model.
            results = remove_old_failed_result(
                results,
                model,
                qid,
            )

            # Add newest result.
            results.append(result)

            # SAVE AFTER EVERY SINGLE QUESTION.
            save_results(results)

            if result["error"] is None:
                completed.add((model, qid))

            # Give the VM a small recovery period.
            time.sleep(1)

        print()
        print(
            f"{model} finished | "
            f"OK: {ok_count} | "
            f"Errors: {error_count}",
            flush=True,
        )

        # Explicitly unload model before loading another.
        unload_model(model)

        # Allow memory to settle.
        time.sleep(5)

    print()
    print("=" * 60)
    print("EVALUATION FINISHED")
    print("=" * 60)
    print(f"Results: {OUTPUT_FILE}")
    print(f"Records: {len(results)}")


if __name__ == "__main__":
    main()
