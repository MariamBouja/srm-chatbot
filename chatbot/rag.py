import functools
import re

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from chatbot.config import (
    COLLECTION_NAME,
    DATA_DIR,
    DB_DIR,
    EMBEDDING_MODEL,
    FALLBACK_RESPONSE,
    MAX_COMPLETION_TOKENS,
    N_RESULTS,
    OPENAI_MODEL,
    SIMILARITY_THRESHOLD,
)
from chatbot.prompts import SYSTEM_PROMPT, build_user_prompt

load_dotenv()

_embedding_model = SentenceTransformer(EMBEDDING_MODEL)
_chroma_client = chromadb.PersistentClient(path=str(DB_DIR))
_collection = _chroma_client.get_collection(name=COLLECTION_NAME)
_openai_client = OpenAI()

_PHONE_RE = re.compile(r"(?<!\d)0\d(?:[\s.\-]?\d{2}){4}(?!\d)")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_URL_RE = re.compile(r"^URL:\s*(\S+)", re.MULTILINE)
_TITLE_RE = re.compile(r"^TITLE:\s*(.+)$", re.MULTILINE)


@functools.lru_cache(maxsize=None)
def get_source_metadata(filename):
    """Resolve a scraped source filename (as stored in chunk metadata) to
    the live page URL/title, read from the URL:/TITLE: header every scraped
    file starts with. Used to turn "sources" into clickable links instead
    of showing raw chunk text to the user."""
    file_path = DATA_DIR / filename
    if not file_path.exists():
        return {"url": None, "title": filename}

    text = file_path.read_text(encoding="utf-8")
    url_match = _URL_RE.search(text)
    title_match = _TITLE_RE.search(text)

    title = title_match.group(1).strip() if title_match else filename
    # Scraped titles are the page's raw <title> tag, e.g. "Mission et
    # métiers – SRM-SM Société Régionale Multiservices Souss-Massa" — strip
    # the repeated site-name suffix so a list of several sources doesn't
    # repeat it every time.
    title = title.split(" – ")[0].strip()

    return {
        "url": url_match.group(1) if url_match else None,
        "title": title,
    }


def retrieve(question, n_results=N_RESULTS):
    query_embedding = _embedding_model.encode(question).tolist()

    results = _collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    return [
        {"document": doc, "metadata": meta, "distance": dist}
        for doc, meta, dist in zip(documents, metadatas, distances)
    ]


def get_contact_info():
    """Extract phone/email/URL from the scraped contact page, if present."""
    contact_file = next(
        (f for f in DATA_DIR.glob("*.txt") if "contact" in f.name.lower()),
        None,
    )
    if contact_file is None:
        return {}

    text = contact_file.read_text(encoding="utf-8")

    url_match = _URL_RE.search(text)

    return {
        "url": url_match.group(1) if url_match else None,
        "phones": sorted(set(_PHONE_RE.findall(text))),
        "emails": sorted(set(_EMAIL_RE.findall(text))),
    }


def build_fallback_message():
    message = FALLBACK_RESPONSE
    contact = get_contact_info()

    details = []
    if contact.get("phones"):
        details.append("Téléphone : " + " / ".join(contact["phones"]))
    if contact.get("emails"):
        details.append("Email : " + " / ".join(contact["emails"]))
    if contact.get("url"):
        details.append("Page Contact : " + contact["url"])

    if details:
        message += "\n\n" + "\n".join(details)

    return message


def generate_answer(question, chunks):
    user_prompt = build_user_prompt(question, chunks)

    response = _openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        max_completion_tokens=MAX_COMPLETION_TOKENS,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    choice = response.choices[0]

    if choice.message.refusal or choice.finish_reason == "content_filter" or not choice.message.content:
        return build_fallback_message()

    return choice.message.content


def answer_question(question, n_results=N_RESULTS):
    chunks = retrieve(question, n_results=n_results)

    best_similarity = max((1 - c["distance"] for c in chunks), default=0.0)

    if best_similarity < SIMILARITY_THRESHOLD:
        return {
            "answer": build_fallback_message(),
            "sources": [],
            "fallback": True,
        }

    answer = generate_answer(question, chunks)

    # The model may still decide, after seeing the retrieved context, that it
    # can't actually answer (retrieval was topically close enough to clear
    # the threshold, but the chunks don't cover the specific question). If it
    # produced our refusal wording, normalize to the fallback built with
    # verified contact details and drop sources — nothing was truly used.
    if answer.strip().startswith(
        "Je suis désolé, mais je ne dispose pas d'informations suffisamment fiables"
    ):
        return {"answer": build_fallback_message(), "sources": [], "fallback": True}

    sources = sorted({c["metadata"]["source"] for c in chunks})

    return {"answer": answer, "sources": sources, "fallback": False}
