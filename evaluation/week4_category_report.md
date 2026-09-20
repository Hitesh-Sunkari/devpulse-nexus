# DevPulse Nexus — Week 4 Category-wise Model Comparison

## Evaluation Design

The same 30 questions were evaluated across all three models. The analysis is performed independently for the seven software-engineering task categories.

**Models:** qwen2.5:1.5b, phi3:mini, tinyllama

**Model loading during scoring:** NONE

## Explanation

| Model | Correctness | Partial | Failure | Relevance | Coverage | Hallucination | Latency | Tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5:1.5b | 0.0% | 50.0% | 50.0% | 25.0% | 13.33% | 25.0% | 70.87s | 529 |
| phi3:mini | 0.0% | 50.0% | 50.0% | 25.0% | 13.33% | 0.0% | 53.19s | 247 |
| tinyllama | 0.0% | 50.0% | 50.0% | 25.0% | 13.33% | 0.0% | 31.96s | 542 |

**Category winner: tinyllama**

## Code Retrieval

| Model | Correctness | Partial | Failure | Relevance | Coverage | Hallucination | Latency | Tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5:1.5b | 0.0% | 75.0% | 25.0% | 43.75% | 54.17% | 0.0% | 315.05s | 242 |
| phi3:mini | 0.0% | 50.0% | 50.0% | 31.25% | 45.83% | 0.0% | 46.36s | 149 |
| tinyllama | 0.0% | 50.0% | 50.0% | 37.5% | 37.5% | 0.0% | 19.6s | 129 |

**Category winner: qwen2.5:1.5b**

## Dependency Understanding

| Model | Correctness | Partial | Failure | Relevance | Coverage | Hallucination | Latency | Tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| phi3:mini | 0.0% | 50.0% | 50.0% | 50.0% | 39.58% | 0.0% | 19.03s | 222 |
| qwen2.5:1.5b | 0.0% | 75.0% | 25.0% | 50.0% | 45.83% | 0.0% | 18.13s | 387 |
| tinyllama | 0.0% | 25.0% | 75.0% | 43.75% | 39.58% | 0.0% | 3.06s | 264 |

**Category winner: qwen2.5:1.5b**

## Bug Analysis

| Model | Correctness | Partial | Failure | Relevance | Coverage | Hallucination | Latency | Tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5:1.5b | 0.0% | 75.0% | 25.0% | 31.25% | 21.67% | 0.0% | 11.23s | 480 |
| tinyllama | 0.0% | 25.0% | 75.0% | 25.0% | 11.25% | 0.0% | 21.82s | 296 |
| phi3:mini | 0.0% | 50.0% | 50.0% | 25.0% | 15.42% | 0.0% | 12.51s | 308 |

**Category winner: qwen2.5:1.5b**

## Code Generation

| Model | Correctness | Partial | Failure | Relevance | Coverage | Hallucination | Latency | Tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5:1.5b | 0.0% | 80.0% | 20.0% | 50.0% | 46.0% | 0.0% | 25.68s | 600 |
| tinyllama | 0.0% | 60.0% | 40.0% | 40.0% | 36.0% | 0.0% | 5.56s | 400 |
| phi3:mini | 0.0% | 20.0% | 80.0% | 30.0% | 18.0% | 0.0% | 20.12s | 400 |

**Category winner: qwen2.5:1.5b**

**Important:** true executable test-pass rate was not captured in the original results. Static code quality is reported separately and must not be called test-pass rate.

## Refactoring

| Model | Correctness | Partial | Failure | Relevance | Coverage | Hallucination | Latency | Tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5:1.5b | 0.0% | 75.0% | 25.0% | 37.5% | 25.0% | 0.0% | 54.83s | 480 |
| tinyllama | 0.0% | 25.0% | 75.0% | 31.25% | 26.25% | 0.0% | 21.97s | 320 |
| phi3:mini | 0.0% | 50.0% | 50.0% | 37.5% | 30.0% | 0.0% | 10.15s | 320 |

**Category winner: phi3:mini**

## RAG-based Question

| Model | Correctness | Partial | Failure | Relevance | Coverage | Hallucination | Latency | Tokens |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen2.5:1.5b | 0.0% | 80.0% | 20.0% | 45.0% | 40.67% | 0.0% | 7.22s | 279 |
| tinyllama | 0.0% | 60.0% | 40.0% | 30.0% | 16.67% | 0.0% | 2.53s | 291 |
| phi3:mini | 0.0% | 80.0% | 20.0% | 30.0% | 27.33% | 0.0% | 29.37s | 242 |

**Category winner: qwen2.5:1.5b**

**Important:** retrieved chunks were not stored in the original results. RAG grounding is therefore reported as answer-to-reference alignment, not retrieval precision/recall.

## Final Category Winners

| Category | Winner |
|---|---|
| Explanation | tinyllama |
| Code Retrieval | qwen2.5:1.5b |
| Dependency Understanding | qwen2.5:1.5b |
| Bug Analysis | qwen2.5:1.5b |
| Code Generation | qwen2.5:1.5b |
| Refactoring | phi3:mini |
| RAG-based Question | qwen2.5:1.5b |

## Interpretation

No single aggregate accuracy number is used as the primary conclusion. Model selection is based on category-specific software-engineering performance.

Latency and token usage are treated as efficiency metrics rather than substitutes for correctness.

Hallucination values are deterministic screening indicators based on forbidden/reference concepts; they are not equivalent to human-reviewed hallucination judgments.

True code test-pass rate and retrieval precision/recall require additional instrumentation because those fields were not captured in the original 90 evaluation records.