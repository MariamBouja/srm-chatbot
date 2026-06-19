import chromadb
from sentence_transformers import SentenceTransformer

DB_DIR = "vector_db"
COLLECTION_NAME = "srm_knowledge"

model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

client = chromadb.PersistentClient(path=DB_DIR)
collection = client.get_collection(name=COLLECTION_NAME)

question = input("Question: ")

query_embedding = model.encode(question).tolist()

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3
)

print("\n--- RESULTS ---\n")

for doc, metadata in zip(results["documents"][0], results["metadatas"][0]):
    print("Source:", metadata["source"])
    print(doc[:1000])
    print("\n----------------\n")