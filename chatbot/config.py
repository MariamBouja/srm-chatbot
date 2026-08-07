from pathlib import Path

# Paths
DATA_DIR = Path("data/website")
DB_DIR = Path("vector_db")
COLLECTION_NAME = "srm_knowledge"
AGENCIES_DATA_PATH = Path("data/agencies.json")

# Embedding model — multilingual (handles the site's French content) and
# lightweight enough to run locally without a GPU.
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Chroma is configured to use cosine distance (see build_vector_db.py) since
# these embeddings are compared by direction, not magnitude — see item 5 in
# the improvement report for the full justification.
DISTANCE_METRIC = "cosine"

# Chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# LLM
OPENAI_MODEL = "gpt-4.1-mini"
MAX_COMPLETION_TOKENS = 1024

# Retrieval
N_RESULTS = 3

# Chroma's cosine "distance" is 1 - cosine_similarity, so it ranges from 0
# (identical direction) to 2 (opposite direction), with 1 meaning unrelated
# (orthogonal) vectors. We convert it to a similarity score in [0, 1] via
# similarity = 1 - distance, and require the *best* retrieved chunk to clear
# this bar before we trust the retrieval enough to call the LLM at all.
# 0.35 was chosen empirically against this corpus (see the audit in the
# improvement report): on-topic questions score ~0.45-0.7, while off-topic
# ones fall below ~0.3.
SIMILARITY_THRESHOLD = 0.35

FALLBACK_RESPONSE = (
    "Je suis désolé, mais je ne dispose pas d'informations suffisamment fiables "
    "pour répondre à votre question.\n\n"
    "Je vous invite à contacter le service client de la SRM-SM ou à consulter la "
    "page Contact du site officiel afin d'obtenir une assistance personnalisée."
)
