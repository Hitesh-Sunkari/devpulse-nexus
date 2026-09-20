import difflib
import json
import os
import re
import time
import urllib.request
import urllib.error
from pathlib import Path

from app.rag import retrieve_context
from app.sourcegraph import search_sourcegraph


# Models used by the live comparison.
# Override with COMPARE_MODELS="model1,model2,model3" when a
# multi-model benchmark is intentionally required.
MODELS = [
    model.strip()
    for model in os.getenv(
        "COMPARE_MODELS",
        "qwen2.5:1.5b,phi3:mini,tinyllama",
    ).split(",")
    if model.strip()
]

CATEGORIES = [
    "Explanation",
    "Code Retrieval",
    "Dependency Understanding",
    "Bug Analysis",
    "Code Generation",
    "Refactoring",
    "RAG-based Question",
]

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://ollama:11434",
).rstrip("/") + "/api/generate"

OLLAMA_TIMEOUT = int(os.getenv("COMPARE_OLLAMA_TIMEOUT", "180"))

STOPWORDS = {
    "what", "does", "the", "this", "that", "how", "where", "when",
    "why", "which", "is", "are", "was", "were", "a", "an", "and",
    "or", "to", "of", "in", "on", "for", "with", "from", "do",
    "can", "could", "would", "should", "my", "your", "it", "its",
}


def _tokens(text):
    words = re.findall(r"[A-Za-z_][A-Za-z0-9_.:/-]{1,}", str(text).lower())
    return {
        word.strip("._:/-")
        for word in words
        if word.strip("._:/-") not in STOPWORDS
    }


def _overlap_score(a, b):
    a_tokens = _tokens(a)
    b_tokens = _tokens(b)

    if not a_tokens:
        return 0.0

    return round(
        100.0 * len(a_tokens & b_tokens) / len(a_tokens),
        2,
    )


def _normalise_question(value):
    return re.sub(
        r"\s+",
        " ",
        str(value).strip().lower(),
    ).strip(" ?!.")


def _load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None


def _walk_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def _find_question_record(data, question):
    if data is None:
        return None

    target = _normalise_question(question)

    for item in _walk_dicts(data):
        candidate = item.get("question")
        if candidate and _normalise_question(candidate) == target:
            return item

    best = None
    best_ratio = 0.0

    for item in _walk_dicts(data):
        candidate = item.get("question")
        if not candidate:
            continue

        ratio = difflib.SequenceMatcher(
            None,
            target,
            _normalise_question(candidate),
        ).ratio()

        if ratio > best_ratio:
            best_ratio = ratio
            best = item

    if best_ratio >= 0.92:
        return best

    return None


def classify_question(question):
    q = question.lower()

    if any(x in q for x in [
        "generate", "write code", "implement", "create endpoint",
        "create function", "write a function",
    ]):
        return "Code Generation"

    if any(x in q for x in [
        "refactor", "improve structure", "clean up", "restructure",
    ]):
        return "Refactoring"

    if any(x in q for x in [
        "bug", "error", "exception", "why does", "fix", "failure",
        "failing", "fails",
    ]):
        return "Bug Analysis"

    if any(x in q for x in [
        "where is", "which file", "implemented", "defined",
        "located", "where does",
    ]):
        return "Code Retrieval"

    if any(x in q for x in [
        "depends", "dependency", "flow", "calls", "relationship",
        "connect", "connected",
    ]):
        return "Dependency Understanding"

    if any(x in q for x in [
        "according to", "docker", "knowledge base", "rag",
        "retrieved knowledge",
    ]):
        return "RAG-based Question"

    return "Explanation"


def _extract_concepts(record):
    if not record:
        return [], []

    expected = (
        record.get("expected")
        or record.get("expected_concepts")
        or record.get("concepts")
        or []
    )

    required = (
        record.get("required")
        or record.get("required_concepts")
        or []
    )

    if isinstance(expected, str):
        expected = [expected]

    if isinstance(required, str):
        required = [required]

    return expected, required


def _concept_score(answer, concepts):
    if not concepts:
        return None

    answer_lower = answer.lower()
    matched = 0

    for concept in concepts:
        concept = str(concept).strip().lower()
        if not concept:
            continue

        if concept in answer_lower:
            matched += 1
            continue

        parts = _tokens(concept)
        if parts and len(parts & _tokens(answer)) >= max(1, len(parts) // 2):
            matched += 1

    return round(100.0 * matched / len(concepts), 2)


def _grounding_score(answer, context):
    if not context:
        return 0.0

    answer_tokens = _tokens(answer)
    context_tokens = _tokens(context)

    if not answer_tokens:
        return 0.0

    return round(
        100.0 * len(answer_tokens & context_tokens) / len(answer_tokens),
        2,
    )


def run_model(model, prompt):
    start = time.perf_counter()

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        # Keep inference bounded on the 4-core / 7.3 GiB VM.
        "options": {
            "num_predict": 96,
            "temperature": 0,
        },
        # Release the model after each request on this resource-constrained VM.
        "keep_alive": "10m",
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=OLLAMA_TIMEOUT,
        ) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        latency = round(time.perf_counter() - start, 2)

        return {
            "model": model,
            "answer": data.get("response", ""),
            "latency_seconds": latency,
            "total_duration_ns": data.get("total_duration"),
            "response_tokens": data.get("eval_count"),
            "prompt_tokens": data.get("prompt_eval_count"),
            "error": None,
        }

    except Exception as exc:
        return {
            "model": model,
            "answer": "",
            "latency_seconds": round(time.perf_counter() - start, 2),
            "total_duration_ns": None,
            "response_tokens": None,
            "prompt_tokens": None,
            "error": str(exc),
        }


def _historical_metrics():
    path = Path("evaluation/week4_final_category_metrics.json")

    data = _load_json(path)

    if not data:
        return {
            "available": False,
            "categories": {},
            "category_winners": {},
        }

    categories = data.get("categories", {})
    winners = data.get("category_winners", {})

    if not winners and isinstance(categories, dict):
        for category, info in categories.items():
            if isinstance(info, dict) and info.get("winner"):
                winners[category] = info["winner"]

    return {
        "available": True,
        "categories": categories,
        "category_winners": winners,
    }


def _historical_for_ui():
    path = Path("evaluation/week4_final_category_metrics.json")

    if not path.exists():
        return {
            category: {"models": {}, "winner": None}
            for category in CATEGORIES
        }

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {
            category: {"models": {}, "winner": None}
            for category in CATEGORIES
        }

    raw_categories = data.get("categories", {})
    output = {}

    for category in CATEGORIES:
        raw = raw_categories.get(category, {})
        models = {}

        for model in MODELS:
            value = raw.get(model, {})
            if not isinstance(value, dict):
                continue

            def first(*keys):
                for key in keys:
                    if value.get(key) is not None:
                        return value.get(key)
                return None

            models[model] = {
                "score": first(
                    "score",
                    "overall_score",
                    "correctness_percent",
                    "correct_percent",
                ),
                "correctness": first(
                    "correctness",
                    "correctness_percent",
                    "correct_percent",
                ),
                "coverage": first(
                    "coverage",
                    "concept_coverage_percent",
                    "average_concept_coverage_percent",
                    "coverage_percent",
                ),
                "hallucination": first(
                    "hallucination",
                    "hallucination_percent",
                    "hallucination_rate_percent",
                ),
                "latency": first(
                    "latency",
                    "latency_seconds",
                ),
            }

        winner = (
            raw.get("winner")
            or raw.get("WINNER")
        )

        if not winner:
            winners = data.get("category_winners", {})
            winner_info = winners.get(category, {})
            if isinstance(winner_info, dict):
                winner = winner_info.get("winner")

        output[category] = {
            "models": models,
            "winner": winner,
        }

    return output


def _build_context(question):
    rag = []
    try:
        rag = retrieve_context(
            question,
            number_of_results=4,
        ) or []
    except Exception as exc:
        rag = [f"RAG retrieval error: {exc}"]

    sourcegraph = search_sourcegraph(
        question,
        limit=8,
    )

    # search_sourcegraph historically returned a list; newer callers may
    # return {"results": [...]}. Normalize both forms.
    if isinstance(sourcegraph, dict):
        source_results = sourcegraph.get("results", []) or []
    else:
        source_results = sourcegraph or []

    context_parts = []

    if rag:
        context_parts.append(
            "KNOWLEDGE BASE:\n" +
            "\n\n".join(str(item) for item in rag)
        )

    if source_results:
        source_parts = []

        for item in source_results:
            repository = item.get("repository", "")
            path = item.get("path", "")
            line = item.get("line", "")
            preview = item.get("preview", "")
            code = item.get("code", "")

            block = (
                f"Repository: {repository}\n"
                f"File: {path}\n"
                f"Line: {line}\n"
                f"Match: {preview}"
            )

            if code:
                block += f"\nRelevant code:\n{code}"

            source_parts.append(block)

        context_parts.append(
            "REPOSITORY SOURCES:\n" +
            "\n\n".join(source_parts)
        )

    context = "\n\n".join(context_parts)

    if not context:
        context = "No relevant context was retrieved."

    return rag, source_results, context


def _build_prompt(question, context):
    return f"""
You are DevPulse Nexus, a repository-aware software engineering assistant.

Answer the user's question using the supplied repository and knowledge-base
context.

Rules:
- Prefer exact repository evidence over guesses.
- Do not invent files, functions, dependencies, or behavior.
- If the context does not establish something, say that it is not established.
- For code questions, mention concrete file/function names when available.
- Keep the answer focused on the user's question.

USER QUESTION:
{question}

CONTEXT:
{context}

ANSWER:
""".strip()


def compare_question(question):
    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    category = classify_question(question)

    rag, sourcegraph, context = _build_context(question)

    prompt = _build_prompt(
        question,
        context,
    )

    reference_data = _load_json(
        "evaluation/reference_answers.json"
    )

    rubric_data = _load_json(
        "evaluation/rubric.json"
    )

    reference_record = _find_question_record(
        reference_data,
        question,
    )

    rubric_record = _find_question_record(
        rubric_data,
        question,
    )

    reference_answer = (
        reference_record.get("reference_answer")
        if reference_record
        else None
    )

    expected, required = _extract_concepts(
        rubric_record
    )

    benchmark_available = bool(
        reference_record and reference_answer
    )

    models = {}

    for model in MODELS:
        result = run_model(
            model,
            prompt,
        )

        answer = result["answer"]

        relevance = _overlap_score(
            question,
            answer,
        )

        grounding = _grounding_score(
            answer,
            context,
        )

        correctness = None
        coverage = None
        hallucination = None

        if benchmark_available:
            correctness = _concept_score(
                answer,
                required or expected,
            )

            coverage = _concept_score(
                answer,
                expected or required,
            )

            if correctness is None:
                correctness = _overlap_score(
                    reference_answer,
                    answer,
                )

            if coverage is None:
                coverage = _overlap_score(
                    reference_answer,
                    answer,
                )

            hallucination_checks = (
                rubric_record.get("hallucination_checks", [])
                if rubric_record
                else []
            )

            if hallucination_checks:
                triggered = sum(
                    1
                    for check in hallucination_checks
                    if str(check).lower() in answer.lower()
                )

                hallucination = round(
                    100.0 * triggered / len(hallucination_checks),
                    2,
                )
            else:
                hallucination = 0.0

            live_score = round(
                0.40 * correctness +
                0.20 * relevance +
                0.20 * coverage +
                0.20 * grounding,
                2,
            )

        else:
            live_score = round(
                0.45 * grounding +
                0.35 * relevance +
                0.20 * min(
                    100.0,
                    100.0 * len(_tokens(answer)) / 120.0,
                ),
                2,
            )

        models[model] = {
            **result,
            "score": live_score,
            "correctness": correctness,
            "relevance": relevance,
            "coverage": coverage,
            "grounding": grounding,
            "hallucination": hallucination,
            "evaluation_basis": (
                "Week 4 benchmark reference + live repository context"
                if benchmark_available
                else "Live repository-aware grounding/relevance heuristic"
            ),
        }

    successful = {
        model: result
        for model, result in models.items()
        if not result.get("error") and result.get("answer")
    }

    best_model = None
    if successful:
        best_model = max(
            successful,
            key=lambda model: successful[model]["score"],
        )

    comparison_reason = None

    if best_model:
        comparison_reason = (
            f"Highest live evaluated score for the {category} question: "
            f"{best_model} ({successful[best_model]['score']:.2f})."
        )

    return {
        "question": question,
        "category": category,
        "benchmark": {
            "available": benchmark_available,
            "reference_answer": reference_answer,
        },
        "models": models,
        "sourcegraph": sourcegraph,
        "rag": {
            "sources": rag,
            "count": len(rag),
        },
        "context": {
            "combined_context_chars": len(context),
        },
        "historical_benchmark": {
            "categories": _historical_for_ui(),
            "category_winners": _historical_metrics()[
                "category_winners"
            ],
        },
        "comparison": {
            "best_model": best_model,
            "reason": comparison_reason,
        },
    }
