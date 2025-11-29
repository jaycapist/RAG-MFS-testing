import os
import json
import uuid
from tenacity import retry, wait_random_exponential, stop_after_attempt
from qdrant_client import QdrantClient
from openai import OpenAI
import numpy
from scripts.chunk_text import chunk_text, truncate_guard
from scripts.upload_embeddings import load_saved_embeddings, upload_to_qdrant

from dotenv import load_dotenv
load_dotenv()

# OpenAI config
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
clientopenai = OpenAI(api_key=OPENAI_API_KEY)

# Qdrant config
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")

# File config
BATCH_FILE = "embeddings.jsonl" # VARIABLE
COLLECTION_NAME = "mfs_collection" # VARIABLE

def batch_iterate(seq, batch_size=64):
    for i in range(0, len(seq), batch_size):
        yield seq[i:i+batch_size]

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(8))
def embed_batch(batch):
    response = clientopenai.embeddings.create(
        model="text-embedding-3-large",
        input=batch
    )
    return [d.embedding for d in response.data]



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
        # Accept dict and LangChain doc
        if isinstance(doc, dict):
            content = doc.get("page_content") or doc.get("content")
            meta = doc.get("metadata", {})
        else:
            # LangChain doc
            content = getattr(doc, "page_content", None)
            meta = getattr(doc, "metadata", {})
        if isinstance(content, str) and content.strip():
            chunks = chunk_text(content, max_tokens=400, overlap=100)
            for i, chunk in enumerate(chunks):
                texts.append(chunk)
                metadatas.append({
                    **meta,
                    "chunk_index": i,
                    "chunk_count": len(chunks),
                })
        else:
            print(f"Doc no content: {doc}")

    print(f"Found {len(texts)} text chunks")

    # Load previously saved embeddings
    saved = load_saved_embeddings()
    saved_texts = {s["text"] for s in saved}

    # Filter out already-embedded chunks
    remaining = [(t, m) for t, m in zip(texts, metadatas) if t not in saved_texts]

    if not remaining:
        print("All chunks already embedded, uploading")
        upload_to_qdrant(saved, qdrant)
        return

    print(f"{len(remaining)} new chunks to embed")

    # Separate texts and metadata for processing
    new_texts, new_metadata = zip(*remaining)
    batches = list(batch_iterate(new_texts, batch_size=64))

    print(f"Created {len(batches)} safe batches")

    meta_index = 0
    new_embeddings_added = False

    for i, batch in enumerate(batches, start=1):
        print(f"Embedding batch: {i}/{len(batches)}")

        safe_batch = []
        safe_meta = []

        for text, meta in zip(batch, new_metadata[meta_index: meta_index + len(batch)]):
            try:
                cleaned = truncate_guard(text)
                safe_batch.append(cleaned)
                safe_meta.append(meta)
            except Exception as e:
                print(f"Skipped problematic chunk: {e}")

        meta_index += len(batch)

        if not safe_batch:
            print(f"All chunks in batch {i} failed, skipping...")
            continue

        try:
            response = embed_batch(safe_batch)
            embeddings = response.tolist() if isinstance(response, numpy.ndarray) else response

            save_embeddings_to_disk(safe_batch, embeddings, safe_meta)
            new_embeddings_added = True
            print(f"Saved {len(safe_batch)} embeddings")
        except Exception as e:
            print(f"Batch {i} failed again: {e}")
            with open("failed_batches.jsonl", "a", encoding="utf-8") as f:
                for text, meta in zip(safe_batch, safe_meta):
                    f.write(json.dumps({"text": text, "metadata": meta}) + "\n")
            continue

    print("Uploading all saved embeddings to Qdrant")
    if new_embeddings_added:
        saved = load_saved_embeddings()
    upload_to_qdrant(saved, qdrant)

    print("Embedding pipeline complete.")



def embed_query(text: str):
    response = clientopenai.embeddings.create(
        input=[text],
        model="text-embedding-3-large"
    )
    return response.data[0].embedding

def load_cached_docs(path="./cache/pdf_cache.json"):
    """Load documents from pdf_cache.json in either list or dict format."""

    if not os.path.exists(path):
        print(f"File not found: {path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        try:
            raw = json.load(f)
        except json.JSONDecodeError:
            print("Failed to decode JSON")
            return []

    docs = []

    if isinstance(raw, list):
        # Existing supported format
        for doc in raw:
            if "page_content" in doc and isinstance(doc["page_content"], str):
                doc.setdefault("metadata", {})
                docs.append(doc)
            else:
                print(f"Skipping invalid document: {doc}")
    elif isinstance(raw, dict):
        # New dict-of-docs format
        for filename, entry in raw.items():
            content = entry.get("content")
            metadata = entry.get("metadata", {})
            if isinstance(content, str) and content.strip():
                docs.append({
                    "page_content": content,
                    "metadata": {
                        "source": filename,
                        **metadata
                    }
                })
            else:
                print(f"Skipping invalid document: {filename}")
    else:
        print("Invalid")
        return []

    return docs

def retry_failed_chunks(path="failed_batches.jsonl"):
    if not os.path.exists(path):
        print("No failed batch file found.")
        return

    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    with open(path, "r", encoding="utf-8") as f:
        data = [json.loads(line) for line in f]

    texts = [truncate_guard(item["text"]) for item in data]
    metas = [item["metadata"] for item in data]

    batches = list(batch_iterate(texts, batch_size=64))
    print(f"Retrying {len(data)} failed chunks in {len(batches)} batches")

    for i, batch in enumerate(batches, start=1):
        try:
            response = embed_batch(batch)
            embeddings = response.tolist() if isinstance(response, numpy.ndarray) else response
            save_embeddings_to_disk(batch, embeddings, metas[(i-1)*64:i*64])
            print(f"Saved batch {i}")
        except Exception as e:
            print(f"Retry failed for batch {i}: {e}")
            continue

    print("Re-uploading all saved embeddings to Qdrant")
    saved = load_saved_embeddings()
    upload_to_qdrant(saved, qdrant)


def main():
    print("Loading documents")
    docs = load_cached_docs() # VARIABLE

    if not docs:
        print("No valid documents")
        return

    print(f"{len(docs)} documents loaded, embedding")
    get_embedding(docs)


if __name__ == "__main__":
    main()
