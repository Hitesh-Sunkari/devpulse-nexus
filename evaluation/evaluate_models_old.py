import json
import time
import requests
from pathlib import Path

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

MODELS = [
    "qwen2.5:1.5b",
    "phi3:mini",
    "tinyllama",
]

QUESTIONS_FILE = Path("evaluation/questions.json")
OUTPUT_FILE = Path("evaluation/results.json")


def load_results():
    if not OUTPUT_FILE.exists():
        return []

    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_results(results):
    temp_file = OUTPUT_FILE.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False
        )

    temp_file.replace(OUTPUT_FILE)


def ask_model(model, question):
    prompt = f"""You are evaluating the DevPulse Nexus application.

Answer this software-engineering question accurately and concisely.

Use only information supported by the DevPulse Nexus codebase
and Docker knowledge provided in the question.

Question:
{question}

Give a concise technical answer.
"""

    start = time.perf_counter()

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "10m",
            "options": {
                "num_predict": 100,
                "temperature": 0.1,
            },
        },
        timeout=120,
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
        "error": None,
    }


def main():

    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    results = load_results()

    completed = {
        (r["id"], r["model"])
        for r in results
        if r.get("error") is None
    }

    total = len(questions) * len(MODELS)

    print(f"Total evaluations: {total}")
    print(f"Already successful: {len(completed)}")
    print(f"Remaining: {total - len(completed)}")
    print()

    for item in questions:

        for model in MODELS:

            key = (item["id"], model)

            if key in completed:
                print(
                    f"SKIP Q{item['id']:02d} | {model}"
                )
                continue

            print(
                f"RUN  Q{item['id']:02d} | {model}",
                flush=True
            )

            try:

                output = ask_model(
                    model,
                    item["question"]
                )

                result = {
                    "id": item["id"],
                    "category": item["category"],
                    "question": item["question"],
                    "model": model,
                    **output,
                }

            except Exception as exc:

                result = {
                    "id": item["id"],
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

            results.append(result)

            # SAVE IMMEDIATELY
            save_results(results)

            if result["error"] is None:
                completed.add(key)

                print(
                    f"     OK | "
                    f"{result['latency_seconds']}s | "
                    f"{result['response_tokens']} tokens",
                    flush=True
                )
            else:
                print(
                    f"     ERROR | {result['error']}",
                    flush=True
                )

            print(
                f"     Saved: {len(results)}/{total}",
                flush=True
            )

    print()
    print("Evaluation complete.")
    print(f"Results saved to: {OUTPUT_FILE}")
    print(f"Total records: {len(results)}")


if __name__ == "__main__":
    main()
