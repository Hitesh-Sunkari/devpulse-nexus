import json
from pathlib import Path

QUESTIONS = Path("evaluation/questions.json")
SOURCE = Path("evaluation/reference_source.txt")
OUTPUT = Path("evaluation/reference_answers.json")


questions = json.loads(
    QUESTIONS.read_text(encoding="utf-8")
)

source = SOURCE.read_text(encoding="utf-8")


# ------------------------------------------------------------------
# IMPORTANT:
# These answers must be based only on the supplied DevPulse source.
# Do not use an LLM here.
# ------------------------------------------------------------------

answers = {
    1: (
        "get_digital_twin() builds a point-in-time representation of "
        "the developer environment. It combines live host telemetry "
        "from get_system_telemetry() with Docker telemetry from "
        "get_docker_metrics(), and adds a current timestamp."
    ),

    2: (
        "DevPulse collects host CPU and memory information using "
        "psutil inside get_system_telemetry(). CPU information includes "
        "usage_percent from psutil.cpu_percent(interval=0.3) and the "
        "CPU core count from psutil.cpu_count(). Memory information "
        "comes from psutil.virtual_memory() and includes total, used, "
        "available memory in GB and memory usage_percent."
    ),

    3: (
        "The deterministic diagnosis analyzes the Digital Twin telemetry "
        "before the LLM runs. build_diagnosis() determines the Docker and "
        "host-memory assessment from telemetry. The LLM is used to explain "
        "the diagnosis rather than determine the diagnosis itself."
    ),

    4: (
        "parse_memory_percentage() converts Docker memory percentage "
        "strings such as '0.26%' into a float. It removes the percent "
        "sign, strips whitespace, and safely returns 0.0 for invalid "
        "values or None."
    ),

    5: (
        "The application creates a FastAPI application with "
        "app = FastAPI(...). The application is configured with the "
        "title 'DevPulse Nexus', a description covering developer "
        "environment observability, Digital Twin telemetry, Docker "
        "monitoring and RAG troubleshooting, and version '1.0.0'."
    ),

    6: (
        "The Ollama generation endpoint is configured as "
        "http://127.0.0.1:11434/api/generate, and the configured model "
        "is qwen2.5:1.5b."
    ),

    7: (
        "The application retrieves RAG context through "
        "retrieve_context imported from app.rag. The configured number "
        "of RAG documents to retrieve is RAG_RESULTS = 2."
    ),

    8: (
        "The Docker monitoring function used by main.py is "
        "get_docker_metrics(), imported from app.docker_monitor."
    ),

    9: (
        "get_system_telemetry() uses psutil to collect host telemetry, "
        "including CPU, memory and disk information. CPU data comes from "
        "psutil.cpu_percent() and psutil.cpu_count(), while memory data "
        "comes from psutil.virtual_memory()."
    ),

    10: (
        "The Digital Twin combines host telemetry and Docker telemetry. "
        "get_digital_twin() returns a dictionary containing a timestamp, "
        "the system telemetry from get_system_telemetry(), and Docker "
        "telemetry from get_docker_metrics()."
    ),

    11: (
        "Docker availability affects diagnosis. If Docker telemetry is "
        "unavailable, the diagnosis marks docker_status as unavailable, "
        "sets Docker container memory to unknown, and reports that Docker "
        "container memory cannot currently be evaluated."
    ),

    12: (
        "SIGNIFICANT_CONTAINER_MEMORY_PERCENT is set to 20.0. The source "
        "describes a container using at least 20 percent of its Docker "
        "memory limit as potentially significant."
    ),

    13: (
        "The deterministic diagnosis runs before the LLM. It analyzes "
        "telemetry and produces the assessment. The source explicitly "
        "states that the LLM explains the diagnosis and does not "
        "determine the diagnosis."
    ),

    14: (
        "When Docker telemetry is unavailable, build_diagnosis() returns "
        "docker_status='unavailable', running_containers=None, "
        "docker_container_memory='unknown', and "
        "docker_is_evidently_responsible='unknown'. The assessment is "
        "also 'unknown' because container memory usage cannot be "
        "evaluated."
    ),

    15: (
        "get_digital_twin() returns a timestamp together with system "
        "telemetry and Docker telemetry. The system telemetry contains "
        "platform, kernel, CPU, memory and disk information."
    ),

    16: (
        "The host memory usage percentage is obtained from "
        "psutil.virtual_memory().percent and stored as "
        "memory['usage_percent'] in get_system_telemetry(). "
        "build_diagnosis() reads that value as host_memory_usage."
    ),

    17: (
        "A FastAPI application can be created with FastAPI(), and the "
        "source configures it with the title 'DevPulse Nexus'."
    ),

    18: (
        "The application should use get_system_telemetry() for host "
        "telemetry and get_docker_metrics() for Docker telemetry, then "
        "combine those values in the Digital Twin returned by "
        "get_digital_twin()."
    ),

    19: (
        "A memory-percentage parser should remove '%' and convert the "
        "remaining value to float. Invalid values should be handled "
        "safely by returning 0.0, as implemented by "
        "parse_memory_percentage()."
    ),

    20: (
        "The deterministic diagnosis should execute before LLM "
        "generation. Telemetry is evaluated first, and the LLM should "
        "explain the resulting diagnosis rather than make the underlying "
        "diagnostic decision."
    ),

    21: (
        "A Docker memory threshold can be represented by "
        "SIGNIFICANT_CONTAINER_MEMORY_PERCENT = 20.0. A container using "
        "20 percent or more of its Docker memory limit is considered "
        "potentially significant."
    ),

    22: (
        "get_digital_twin() can be kept focused on assembling the "
        "point-in-time representation: timestamp, system telemetry and "
        "Docker telemetry. Host telemetry collection belongs in "
        "get_system_telemetry(), while Docker collection belongs in "
        "get_docker_metrics()."
    ),

    23: (
        "parse_memory_percentage() provides a small, defensive "
        "conversion boundary: None and invalid values return 0.0, "
        "while strings containing a percentage are converted to float "
        "after removing the percent sign."
    ),

    24: (
        "The diagnosis logic should remain deterministic and separate "
        "from LLM explanation. build_diagnosis() should inspect the "
        "Digital Twin and explicitly handle unavailable Docker telemetry "
        "and the no-container case."
    ),

    25: (
        "The code can be refactored by keeping configuration values such "
        "as RAG_RESULTS, OLLAMA_TIMEOUT and "
        "SIGNIFICANT_CONTAINER_MEMORY_PERCENT at the configuration "
        "level, while keeping telemetry collection and diagnosis in "
        "separate functions."
    ),

    26: (
        "The source describes RAG as part of DevPulse's troubleshooting "
        "capability and imports retrieve_context from app.rag."
    ),

    27: (
        "The configured RAG result count is RAG_RESULTS = 2, meaning the "
        "application is configured to retrieve two RAG documents."
    ),

    28: (
        "RAG context retrieval is performed through the "
        "retrieve_context function imported from app.rag."
    ),

    29: (
        "The source does not support the claim that Docker is always "
        "responsible for high host memory usage. The deterministic "
        "diagnosis explicitly reports Docker responsibility as unknown "
        "when Docker telemetry is unavailable."
    ),

    30: (
        "No. The retrieved knowledge/source does not establish that "
        "Docker is always responsible for high host memory usage. "
        "The diagnosis is based on telemetry, and when Docker telemetry "
        "is unavailable the Docker responsibility assessment is "
        "'unknown'."
    ),
}


if len(answers) != len(questions):
    raise RuntimeError(
        f"Expected {len(questions)} answers, generated {len(answers)}"
    )

question_ids = {q["id"] for q in questions}

if set(answers) != question_ids:
    raise RuntimeError(
        f"Answer IDs do not match question IDs.\n"
        f"Missing: {sorted(question_ids - set(answers))}\n"
        f"Extra: {sorted(set(answers) - question_ids)}"
    )


output = []

for q in questions:
    output.append({
        "id": q["id"],
        "category": q["category"],
        "question": q["question"],
        "reference_answer": answers[q["id"]],
    })


OUTPUT.write_text(
    json.dumps(output, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("=" * 80)
print("REFERENCE ANSWERS CREATED")
print("=" * 80)
print("Questions:", len(output))
print("Non-empty:", sum(bool(x["reference_answer"].strip()) for x in output))
print("Source:", SOURCE)
print("Output:", OUTPUT)
print("Model loading: NONE")
print("=" * 80)
