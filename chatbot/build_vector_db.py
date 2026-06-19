from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

DATA_DIR = Path("data/website")
DB_DIR = Path("vector_db")
COLLECTION_NAME = "srm_knowledge"

model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


def chunk_text(text, chunk_size=1000, overlap=150):
    paragraphs = text.split("\n")
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) < chunk_size:
            current_chunk += paragraph + "\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def main():
    client = chromadb.PersistentClient(path=str(DB_DIR))

    collection = client.get_or_create_collection(name=COLLECTION_NAME)

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