
import os
import re
import urllib.request
import json

SOURCEGRAPH_URL = os.getenv(
    "SOURCEGRAPH_URL",
    "http://host.docker.internal:7080",
).rstrip("/")

SOURCEGRAPH_TOKEN = os.getenv("SG_TOKEN", "")


def _request(query):
    graphql = """
    query Search($query: String!) {
      search(query: $query) {
        results {
          matchCount
          limitHit
          results {
            __typename
            ... on FileMatch {
              repository { name }
              file { path }
              lineMatches {
                preview
                lineNumber
              }
            }
          }
        }
      }
    }
    """

    body = json.dumps({
        "query": graphql,
        "variables": {"query": query},
    }).encode()

    headers = {
        "Content-Type": "application/json",
    }

    if SOURCEGRAPH_TOKEN:
        headers["Authorization"] = f"token {SOURCEGRAPH_TOKEN}"

    req = urllib.request.Request(
        f"{SOURCEGRAPH_URL}/.api/graphql",
        data=body,
        headers=headers,
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=20) as response:
        data = json.loads(response.read().decode())

    if data.get("errors"):
        raise RuntimeError(str(data["errors"]))

    return data


def search_sourcegraph(query, limit=8):
    queries = [query.strip()]

    # Natural-language questions often search poorly in Sourcegraph.
    # Extract identifiers/file names and use those as a fallback.
    identifiers = re.findall(
        r'\b[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)?\b',
        query,
    )

    useful = [
        x for x in identifiers
        if (
            "_" in x
            or "." in x
            or x in {
                "FastAPI", "Docker", "ChromaDB",
                "Ollama", "Sourcegraph", "RAG",
            }
        )
    ]

    if useful:
        queries.append(" OR ".join(useful[:6]))

    seen = set()
    sources = []

    for search_query in queries:
        try:
            data = _request(search_query)
        except Exception:
            continue

        results = (
            data.get("data", {})
                .get("search", {})
                .get("results", {})
                .get("results", [])
        )

        for item in results:
            if item.get("__typename") != "FileMatch":
                continue

            repo = item.get("repository") or {}
            file_info = item.get("file") or {}

            repository = repo.get("name")
            path = file_info.get("path")

            for match in item.get("lineMatches", []):
                line_number = match.get("lineNumber")
                file_content = file_info.get("content") or ""

                code = ""
                if file_content and isinstance(line_number, int):
                    lines = file_content.splitlines()
                    start_line = max(0, line_number - 8)
                    end_line = min(len(lines), line_number + 13)
                    code = "\n".join(
                        f"{i + 1}: {lines[i]}"
                        for i in range(start_line, end_line)
                    )

                record = {
                    "repository": repository,
                    "path": path,
                    "line": line_number,
                    "preview": match.get("preview"),
                    "code": code,
                }

                key = (
                    repository,
                    path,
                    record["line"],
                    record["preview"],
                )

                if key not in seen:
                    seen.add(key)
                    sources.append(record)

                if len(sources) >= limit:
                    return sources

    return sources
