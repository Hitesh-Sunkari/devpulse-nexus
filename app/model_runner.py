
import os
import time
import urllib.request
import urllib.error
import json

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_URL",
    "http://ollama:11434",
).rstrip("/")

if OLLAMA_BASE_URL.endswith("/api/generate"):
    OLLAMA_GENERATE_URL = OLLAMA_BASE_URL
else:
    OLLAMA_GENERATE_URL = OLLAMA_BASE_URL + "/api/generate"


# Models used by the live comparison.
# Run sequentially so only one model is actively loaded at a time.
OLLAMA_MODELS = [
    "qwen2.5:1.5b",
]


def run_model(model, prompt, timeout=None):
    start = time.perf_counter()

    if timeout is None:
        timeout = int(os.getenv("OLLAMA_TIMEOUT", "90"))

    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        # Keep the model warm between sequential comparison requests.
        "keep_alive": "10m",
        "options": {
            "num_predict": 64,
            "temperature": 0,
        },
    }).encode()

    request = urllib.request.Request(
        OLLAMA_GENERATE_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            data = json.loads(
                response.read().decode()
            )

        latency = time.perf_counter() - start

        return {
            "model": model,
            "answer": data.get("response", ""),
            "latency_seconds": round(latency, 2),
            "total_duration_ns": data.get("total_duration"),
            "load_duration_ns": data.get("load_duration"),
            "eval_duration_ns": data.get("eval_duration"),
            "response_tokens": data.get("eval_count"),
            "error": None,
        }

    except Exception as exc:
        latency = time.perf_counter() - start

        return {
            "model": model,
            "answer": "",
            "latency_seconds": round(latency, 2),
            "total_duration_ns": None,
            "load_duration_ns": None,
            "eval_duration_ns": None,
            "response_tokens": None,
            "error": str(exc),
        }


def run_all_models(prompt):
    results = {}

    for model in OLLAMA_MODELS:
        results[model] = run_model(model, prompt)

    return results
