import chromadb
from chromadb.errors import NotFoundError
from sentence_transformers import SentenceTransformer

from chatbot.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    COLLECTION_NAME,
    DATA_DIR,
    DB_DIR,
    DISTANCE_METRIC,
    EMBEDDING_MODEL,
)

model = SentenceTransformer(EMBEDDING_MODEL)


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    paragraphs = [p for p in text.split("\n") if p.strip()]
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        if current_chunk and len(current_chunk) + len(paragraph) + 1 >= chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = current_chunk[-overlap:] if overlap > 0 else ""

        current_chunk += paragraph + "\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def main():
    client = chromadb.PersistentClient(path=str(DB_DIR))

    # Rebuild from scratch each run so the collection always exactly mirrors
    # data/website — this is what guarantees no stale/orphaned embeddings
    # survive a rebuild (see the vector DB audit in the improvement report).
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except NotFoundError:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": DISTANCE_METRIC},
    )

    files = list(DATA_DIR.glob("*.txt"))

    print(f"Files found: {len(files)}")

    doc_id = 0

    for file in files:
        text = file.read_text(encoding="utf-8")
        chunks = chunk_text(text)

        for chunk in chunks:
            embedding = model.encode(chunk).tolist()

            collection.add(
                ids=[f"doc_{doc_id}"],
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[{"source": file.name}],
            )

            doc_id += 1

    print(f"Chunks stored: {doc_id}")
    print("Vector database created successfully.")


if __name__ == "__main__":
    main()