import json

from app.rag import retrieve_context


def orchestrate_request(
    question,
    digital_twin,
    diagnosis,
    rag_results=2,
):
    """
    Coordinate the major DevPulse Nexus services.

    Flow:
    User Question
        -> RAG Retrieval
        -> Context
        -> LLM-ready request

    Telemetry and diagnosis are supplied by the
    application service because they are authoritative.
    """

    documents = retrieve_context(
        question,
        number_of_results=rag_results,
    )

    context = (
        "\n\n".join(documents)
        if documents
        else "No relevant knowledge was retrieved."
    )

    return {
        "question": question,

        "services": {
            "application_service": "FastAPI",
            "orchestration_service": "DevPulse Orchestrator",
            "retrieval_service": "RAG + ChromaDB",
            "knowledge_service": "knowledge/docker.md",
            "embedding_service": "all-MiniLM-L6-v2",
            "llm_service": "Ollama",
            "llm_model": "qwen2.5:1.5b",
        },

        "pipeline": [
            "User Question",
            "Application Service",
            "Orchestration Service",
            "RAG Retrieval Service",
            "Relevant Context",
            "LLM Service",
            "Ollama",
            "Qwen 2.5 1.5B",
            "Response",
        ],

        "digital_twin": digital_twin,

        "diagnosis": diagnosis,

        "retrieved_context": documents,

        "llm_context": context,
    }
