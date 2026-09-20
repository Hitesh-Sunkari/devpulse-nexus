
CATEGORIES = [
    "Explanation",
    "Code Retrieval",
    "Dependency Understanding",
    "Bug Analysis",
    "Code Generation",
    "Refactoring",
    "RAG-based Question",
]


def classify_question(question):
    q = question.lower()

    if any(x in q for x in [
        "generate",
        "write code",
        "implement",
        "create endpoint",
        "create a function",
        "add an endpoint",
    ]):
        return "Code Generation"

    if any(x in q for x in [
        "refactor",
        "improve structure",
        "clean up",
        "restructure",
        "simplify the code",
    ]):
        return "Refactoring"

    if any(x in q for x in [
        "bug",
        "error",
        "exception",
        "why does",
        "why is",
        "fix",
        "fails",
        "failure",
    ]):
        return "Bug Analysis"

    if any(x in q for x in [
        "where is",
        "which file",
        "implemented",
        "defined",
        "located",
        "find the function",
    ]):
        return "Code Retrieval"

    if any(x in q for x in [
        "depends",
        "dependency",
        "dependencies",
        "flow",
        "calls",
        "relationship",
        "connected to",
    ]):
        return "Dependency Understanding"

    if any(x in q for x in [
        "according to",
        "knowledge base",
        "docker memory",
        "docker documentation",
        "what does the knowledge",
    ]):
        return "RAG-based Question"

    return "Explanation"
