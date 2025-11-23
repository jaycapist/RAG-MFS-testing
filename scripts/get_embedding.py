import os
import json
import time
import uuid
from tenacity import retry, wait_random_exponential, stop_after_attempt
from qdrant_client import QdrantClient
from scripts.chunk_text import chunk_text
from scripts.upload_embeddings import load_saved_embeddings, upload_to_qdrant

from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer

from dotenv import load_dotenv
load_dotenv()

# Environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")

# Models
bge_model = SentenceTransformer("BAAI/bge-large-en-v1.5")
bge_tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-large-en-v1.5")

# Constants
MAX_TOKENS = 200_000
MAX_CHUNK_TOKENS = 8191  # BGE maximum input length
BATCH_FILE = "embeddings.jsonl"
COLLECTION_NAME = "mfs_collection"


def num_tokens(text):
    return len(bge_tokenizer.encode(text))


def safe_batches(texts):
    """Yield batches that stay within safe token and memory limits."""
    batches, current_batch, current_tokens = [], [], 0

    for text in texts:
        tokens = bge_tokenizer.encode(text)

        # Truncate oversized chunks
        if len(tokens) > MAX_CHUNK_TOKENS:
            print(f"Truncating oversized chunk ({len(tokens)} tokens)")
            tokens = tokens[:MAX_CHUNK_TOKENS]
            text = bge_tokenizer.decode(tokens)

        if current_tokens + len(tokens) > MAX_TOKENS:
            batches.append(current_batch)
            current_batch = [text]
            current_tokens = len(tokens)
        else:
            current_batch.append(text)
            current_tokens += len(tokens)

    if current_batch:
        batches.append(current_batch)

    return batches


@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(8))
def embed_batch(batch):
    """Embed a list of strings with BGE."""
    return bge_model.encode(batch, normalize_embeddings=True)


def save_embeddings_to_disk(texts, embeddings, metadata_list, path="embeddings.jsonl"):
    with open(path, "a", encoding="utf-8") as f:
        for i in range(len(texts)):
            entry = {
                "id": str(uuid.uuid4()),
                "text": texts[i],
                "embedding": embeddings[i],
                "metadata": metadata_list[i],
            }
            f.write(json.dumps(entry) + "\n")


def get_embedding(docs):
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    print("Preparing documents:")

    texts, metadatas = [], []
    for doc in docs:
        if hasattr(doc, "page_content") and isinstance(doc.page_content, str):
            chunks = chunk_text(doc.page_content)
            texts.extend(chunks)
            metadatas.extend([doc.metadata] * len(chunks))

    print(f"Found {len(texts)} text chunks")

    # Load previously saved embeddings
    saved = load_saved_embeddings()
    saved_texts = {s["text"] for s in saved}

    # Filter out already-embedded chunks
    remaining = [(t, m) for t, m in zip(texts, metadatas) if t not in saved_texts]

    if not remaining:
        print("All chunks already embedded, uploading existing data.")
        upload_to_qdrant(saved, qdrant)
        return

    print(f"{len(remaining)} new chunks to embed")

    # Separate texts & metadata for processing
    new_texts, new_metadata = zip(*remaining)
    batches = safe_batches(new_texts)

    print(f"Created {len(batches)} safe batches")

    meta_index = 0

    # Embed each batch
    for i, batch in enumerate(batches, start=1):
        print(f"Embedding batch {i}/{len(batches)} ({len(batch)} chunks)")

        try:
            response = embed_batch(batch)
            embeddings = response.tolist()

            batch_metas = new_metadata[meta_index: meta_index + len(batch)]
            meta_index += len(batch)

            save_embeddings_to_disk(batch, embeddings, batch_metas)
            print(f"Saved {len(batch)} embeddings")

            time.sleep(1)

        except Exception as e:
            print(f"Failed batch {i}: {e}")
            continue

    print("Uploading all saved embeddings to Qdrant...")
    all_data = load_saved_embeddings()
    upload_to_qdrant(all_data, qdrant)

    print("Embedding pipeline complete.")


def embed_query(text: str):
    """Embed a single query string."""
    return bge_model.encode(text, normalize_embeddings=True).tolist()
