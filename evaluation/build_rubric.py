import json
from pathlib import Path

QUESTIONS = Path("evaluation/questions.json")
SOURCE = Path("evaluation/reference_source.txt")
OUTPUT = Path("evaluation/rubric.json")

questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
source = SOURCE.read_text(encoding="utf-8")

# Ground-truth rubric derived from the actual project source/knowledge base.
# These are evaluation criteria, not model-generated answers.

rubric_data = {
1: {
    "expected": [
        "get_digital_twin",
        "collects host/system telemetry",
        "CPU",
        "memory",
        "Docker/container information",
        "returns a digital-twin representation"
    ],
    "required": ["get_digital_twin", "telemetry"],
    "forbidden": ["invented device identifier", "MAC address", "external digital twin service"]
},
2: {
    "expected": [
        "host CPU information",
        "host memory information",
        "psutil",
        "CPU percentage",
        "memory percentage"
    ],
    "required": ["CPU", "memory"],
    "forbidden": []
},
3: {
    "expected": [
        "deterministic diagnosis",
        "rule-based diagnosis",
        "uses telemetry/state",
        "consistent diagnosis",
        "does not depend on LLM"
    ],
    "required": ["deterministic", "diagnosis"],
    "forbidden": []
},
4: {
    "expected": [
        "orchestrator",
        "coordinates",
        "RAG retrieval",
        "diagnosis",
        "Ollama",
        "final response"
    ],
    "required": ["orchestrator"],
    "forbidden": []
},
5: {
    "expected": ["rag.py", "ChromaDB", "retrieval"],
    "required": ["rag.py"],
    "forbidden": []
},
6: {
    "expected": ["docker_monitor.py", "Docker", "container statistics"],
    "required": ["docker_monitor.py"],
    "forbidden": []
},
7: {
    "expected": ["orchestrator.py", "Ollama", "model configuration"],
    "required": ["Ollama"],
    "forbidden": []
},
8: {
    "expected": ["telemetry_history.py", "telemetry history"],
    "required": ["telemetry_history.py"],
    "forbidden": []
},
9: {
    "expected": [
        "FastAPI",
        "/ask",
        "orchestrator",
        "RAG",
        "diagnosis",
        "Ollama"
    ],
    "required": ["/ask", "RAG", "Ollama"],
    "forbidden": []
},
10: {
    "expected": [
        "user question",
        "FastAPI",
        "orchestrator",
        "telemetry",
        "diagnosis",
        "retrieval",
        "Ollama",
        "final answer"
    ],
    "required": ["question", "Ollama"],
    "forbidden": []
},
11: {
    "expected": ["orchestrate_request", "RAG", "knowledge retrieval", "rag"],
    "required": ["orchestrate_request", "rag"],
    "forbidden": []
},
12: {
    "expected": [
        "retrieved documents",
        "context",
        "prompt",
        "passed to Ollama"
    ],
    "required": ["retrieved"],
    "forbidden": []
},
13: {
    "expected": [
        "Docker unavailable",
        "error handling",
        "empty/no container data",
        "host telemetry can still be used",
        "Docker should not automatically be blamed"
    ],
    "required": ["Docker"],
    "forbidden": []
},
14: {
    "expected": [
        "timeout",
        "Ollama",
        "exception/error handling",
        "request fails gracefully"
    ],
    "required": ["timeout", "Ollama"],
    "forbidden": []
},
15: {
    "expected": [
        "ChromaDB",
        "embedding",
        "query",
        "collection",
        "no matching documents",
        "retrieval configuration"
    ],
    "required": ["retrieval"],
    "forbidden": []
},
16: {
    "expected": [
        "host memory",
        "container memory",
        "running containers",
        "deterministic diagnosis",
        "container usage must support responsibility"
    ],
    "required": ["host memory", "container"],
    "forbidden": []
},
17: {
    "expected": [
        "iterate over containers",
        "memory percentage",
        "average",
        "handle empty list / zero containers"
    ],
    "required": ["average", "memory"],
    "forbidden": []
},
18: {
    "expected": [
        "iterate containers",
        "memory percentage",
        "> 50",
        "filter/identify containers"
    ],
    "required": ["> 50", "memory"],
    "forbidden": []
},
19: {
    "expected": [
        "parse_memory_percentage",
        "test function",
        "valid memory input",
        "expected percentage",
        "pytest/assert"
    ],
    "required": ["parse_memory_percentage", "assert"],
    "forbidden": []
},
20: {
    "expected": [
        "zero running containers",
        "not_responsible",
        "test",
        "assert"
    ],
    "required": ["not_responsible", "assert"],
    "forbidden": []
},
21: {
    "expected": [
        "FastAPI",
        "GET endpoint",
        "latest telemetry history",
        "telemetry history",
        "return latest record"
    ],
    "required": ["FastAPI", "GET", "latest"],
    "forbidden": []
},
22: {
    "expected": [
        "build_diagnosis",
        "separate pure logic",
        "dependency injection",
        "small testable functions",
        "mock inputs"
    ],
    "required": ["build_diagnosis", "test"],
    "forbidden": []
},
23: {
    "expected": [
        "environment variables",
        "os.getenv",
        "Ollama URL",
        "model name",
        "configuration"
    ],
    "required": ["environment", "Ollama"],
    "forbidden": []
},
24: {
    "expected": [
        "duplicate Digital Twin logic",
        "single shared function/module",
        "reuse",
        "remove duplication"
    ],
    "required": ["duplicate", "reuse"],
    "forbidden": []
},
25: {
    "expected": [
        "orchestrator.py",
        "specific exception handling",
        "timeouts",
        "logging",
        "graceful fallback"
    ],
    "required": ["exception", "orchestrator"],
    "forbidden": []
},
26: {
    "expected": [
        "docker stats",
        "live container resource usage"
    ],
    "required": ["docker stats"],
    "forbidden": []
},
27: {
    "expected": [
        "docker stats",
        "identify high-memory containers",
        "compare container memory with host memory",
        "inspect processes/logs/configuration",
        "do not automatically blame Docker"
    ],
    "required": ["docker stats"],
    "forbidden": []
},
28: {
    "expected": [
        "--memory",
        "memory limit",
        "docker run"
    ],
    "required": ["--memory"],
    "forbidden": []
},
29: {
    "expected": [
        "container memory usage",
        "docker stats",
        "processes",
        "logs",
        "memory limits",
        "host memory"
    ],
    "required": ["container", "memory"],
    "forbidden": []
},
30: {
    "expected": [
        "Docker is not always responsible",
        "host memory can have other causes",
        "container usage must be examined",
        "evidence-based diagnosis"
    ],
    "required": ["not always", "host memory"],
    "forbidden": []
}
}

# Category-specific scoring configuration.
category_rules = {
    "Explanation": {
        "correctness_weight": 0.60,
        "relevance_weight": 0.25,
        "hallucination_weight": 0.15,
    },
    "Code Retrieval": {
        "correctness_weight": 0.65,
        "relevance_weight": 0.20,
        "hallucination_weight": 0.15,
    },
    "Dependency Understanding": {
        "correctness_weight": 0.55,
        "relevance_weight": 0.25,
        "hallucination_weight": 0.20,
    },
    "Bug Analysis": {
        "correctness_weight": 0.50,
        "relevance_weight": 0.25,
        "hallucination_weight": 0.25,
    },
    "Code Generation": {
        "correctness_weight": 0.45,
        "relevance_weight": 0.15,
        "hallucination_weight": 0.10,
        "test_pass_weight": 0.30,
    },
    "Refactoring": {
        "correctness_weight": 0.55,
        "relevance_weight": 0.25,
        "hallucination_weight": 0.20,
    },
    "RAG-based Question": {
        "correctness_weight": 0.40,
        "relevance_weight": 0.20,
        "hallucination_weight": 0.20,
        "retrieval_quality_weight": 0.20,
    },
}

rubric = []

for q in questions:
    item = {
        "id": q["id"],
        "category": q["category"],
        "question": q["question"],
        "expected_concepts": rubric_data[q["id"]]["expected"],
        "required_concepts": rubric_data[q["id"]]["required"],
        "hallucination_checks": rubric_data[q["id"]]["forbidden"],
        "category_metrics": category_rules[q["category"]],
        "scoring": {
            "correct": 1.0,
            "partial": 0.5,
            "incorrect": 0.0
        }
    }

    if q["category"] == "Code Generation":
        item["test_pass_required"] = True

    if q["category"] == "RAG-based Question":
        item["retrieval_required"] = True

    rubric.append(item)

OUTPUT.write_text(
    json.dumps(rubric, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("=" * 78)
print("RUBRIC CREATED")
print("=" * 78)
print("Questions:", len(rubric))
print("Expected concepts:", sum(len(x["expected_concepts"]) for x in rubric))
print("Required concepts:", sum(len(x["required_concepts"]) for x in rubric))
print()
print("Categories:")
from collections import Counter
print(Counter(x["category"] for x in rubric))
print()
print("Saved:", OUTPUT)
print("Model loading: NONE")
