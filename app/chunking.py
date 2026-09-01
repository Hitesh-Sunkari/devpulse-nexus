from pathlib import Path


def load_document(file_path):
    return Path(file_path).read_text(encoding="utf-8")


def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())

        start += chunk_size - overlap

    return chunks


if __name__ == "__main__":
    file_path = "knowledge/docker.md"

    text = load_document(file_path)

    chunks = chunk_text(text)

    print(f"Document length: {len(text)} characters")
    print(f"Number of chunks: {len(chunks)}")

    for i, chunk in enumerate(chunks, start=1):
        print("\n" + "=" * 60)
        print(f"CHUNK {i}")
        print("=" * 60)
        print(chunk)
