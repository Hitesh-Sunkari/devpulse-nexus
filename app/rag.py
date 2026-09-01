import chromadb

from sentence_transformers import SentenceTransformer


DB_PATH = "./chroma_db"
MODEL_NAME = "all-MiniLM-L6-v2"


client = chromadb.PersistentClient(path=DB_PATH)

collection = client.get_collection(
    name="devpulse_knowledge"
)

model = SentenceTransformer(MODEL_NAME)


def retrieve_context(question, number_of_results=2):

    question_embedding = model.encode(
        [question]
    )[0].tolist()

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=number_of_results
    )

    documents = results["documents"][0]

    return documents


if __name__ == "__main__":

    question = "How can I investigate high Docker memory usage?"

    documents = retrieve_context(question)

    print("\nQuestion:")
    print(question)

    print("\nRetrieved knowledge:")

    for i, document in enumerate(documents, start=1):

        print("\n" + "=" * 60)
        print(f"RESULT {i}")
        print("=" * 60)
        print(document)
