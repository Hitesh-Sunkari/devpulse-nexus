# DevPulse Nexus - Week 4 Category-Wise Model Comparison

## Evaluation design

- 30 identical evaluation questions were applied to all 3 models.
- 90 total model evaluations were analyzed.
- 7 software-engineering task categories were evaluated separately.
- Scoring was performed without loading any model.
- Correctness uses the predefined reference-concept rubric.
- Hallucination is a deterministic screening signal, not human proof.

## Explanation

| Model | Correctness | Partial | Failure | Relevance | Coverage | Hallucination | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5:1.5b | 75.00% | 25.00% | 0.00% | 87.50% | 28.33% | 25.00% | 70.87s |
| phi3:mini | 75.00% | 25.00% | 0.00% | 87.50% | 23.33% | 0.00% | 53.19s |
| tinyllama | 75.00% | 25.00% | 0.00% | 87.50% | 28.33% | 0.00% | 31.96s |

**Category winner: tinyllama**

## Code Retrieval

| Model | Correctness | Partial | Failure | Relevance | Coverage | Hallucination | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5:1.5b | 50.00% | 0.00% | 50.00% | 50.00% | 75.00% | 0.00% | 315.05s |
| phi3:mini | 50.00% | 0.00% | 50.00% | 50.00% | 58.33% | 0.00% | 46.36s |
| tinyllama | 25.00% | 0.00% | 75.00% | 25.00% | 37.50% | 0.00% | 19.60s |

**Category winner: qwen2.5:1.5b**

## Dependency Understanding

| Model | Correctness | Partial | Failure | Relevance | Coverage | Hallucination | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| phi3:mini | 50.00% | 50.00% | 0.00% | 75.00% | 42.71% | 0.00% | 19.03s |
| qwen2.5:1.5b | 50.00% | 50.00% | 0.00% | 75.00% | 45.83% | 0.00% | 18.13s |
| tinyllama | 50.00% | 25.00% | 25.00% | 62.50% | 39.58% | 0.00% | 3.06s |

**Category winner: qwen2.5:1.5b**

## Bug Analysis

| Model | Correctness | Partial | Failure | Relevance | Coverage | Hallucination | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5:1.5b | 100.00% | 0.00% | 0.00% | 100.00% | 35.83% | 0.00% | 11.23s |
| tinyllama | 50.00% | 50.00% | 0.00% | 75.00% | 16.25% | 0.00% | 21.82s |
| phi3:mini | 75.00% | 25.00% | 0.00% | 87.50% | 25.42% | 0.00% | 12.51s |

**Category winner: qwen2.5:1.5b**

## Code Generation

| Model | Correctness | Partial | Failure | Relevance | Coverage | Hallucination | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5:1.5b | 60.00% | 40.00% | 0.00% | 80.00% | 63.00% | 0.00% | 25.68s |
| tinyllama | 20.00% | 80.00% | 0.00% | 60.00% | 44.00% | 0.00% | 5.56s |
| phi3:mini | 20.00% | 80.00% | 0.00% | 60.00% | 35.00% | 0.00% | 20.12s |

**Category winner: qwen2.5:1.5b**

**Executable test-pass rate:** Not available from the existing results because generated code was not stored/executed as test artifacts.

## Refactoring

| Model | Correctness | Partial | Failure | Relevance | Coverage | Hallucination | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5:1.5b | 50.00% | 25.00% | 25.00% | 62.50% | 36.25% | 0.00% | 54.83s |
| tinyllama | 75.00% | 25.00% | 0.00% | 87.50% | 26.25% | 0.00% | 21.97s |
| phi3:mini | 75.00% | 25.00% | 0.00% | 87.50% | 41.25% | 0.00% | 10.15s |

**Category winner: phi3:mini**

## RAG-based Question

| Model | Correctness | Partial | Failure | Relevance | Coverage | Hallucination | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5:1.5b | 100.00% | 0.00% | 0.00% | 100.00% | 56.33% | 0.00% | 7.22s |
| tinyllama | 40.00% | 20.00% | 40.00% | 50.00% | 28.33% | 0.00% | 2.53s |
| phi3:mini | 100.00% | 0.00% | 0.00% | 100.00% | 39.00% | 0.00% | 29.37s |

**Category winner: qwen2.5:1.5b**

**Retrieval precision/recall:** Not available because retrieved documents/chunks were not stored in results.json.

## Final category winners

- **Explanation:** tinyllama
- **Code Retrieval:** qwen2.5:1.5b
- **Dependency Understanding:** qwen2.5:1.5b
- **Bug Analysis:** qwen2.5:1.5b
- **Code Generation:** qwen2.5:1.5b
- **Refactoring:** phi3:mini
- **RAG-based Question:** qwen2.5:1.5b

## Important limitations

The existing 90 result records contain model answers, latency and token statistics, but do not contain retrieval documents/chunks or executable generated-code test results.
Therefore retrieval precision/recall and executable code test-pass rate are reported as unavailable rather than invented.