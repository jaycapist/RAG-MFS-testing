import os
import json
import time
import uuid
from tenacity import retry, wait_random_exponential, stop_after_attempt
from openai import OpenAI
from qdrant_client import QdrantClient
from scripts.chunk_text import chunk_text
import tiktoken
from scripts.upload_embeddings import load_saved_embeddings, upload_to_qdrant

from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")

clientopenai = OpenAI(api_key=OPENAI_API_KEY)
tokenizer = tiktoken.encoding_for_model("text-embedding-3-large")

MAX_TOKENS = 200_000
MAX_CHUNK_TOKENS = 8191
BATCH_FILE = "embeddings.jsonl"
COLLECTION_NAME = "mfs_collection"

def num_tokens(text):
    return len(tokenizer.encode(text))

MAX_CHUNK_TOKENS = 8191

def safe_batches(texts):
    """Yield batches that respect token and size limits."""
    batches, current_batch, current_tokens = [], [], 0
    for text in texts:
        tokens = tokenizer.encode(text)
        if len(tokens) > MAX_CHUNK_TOKENS:
            print(f"Truncating oversized chunk ({len(tokens)} tokens)")
            text = tokenizer.decode(tokens[:MAX_CHUNK_TOKENS])
            tokens = tokens[:MAX_CHUNK_TOKENS]

        if current_tokens + len(tokens) > MAX_TOKENS:
            batches.append(current_batch)
            current_batch, current_tokens = [text], len(tokens)
        else:
            current_batch.append(text)
            current_tokens += len(tokens)

    if current_batch:
        batches.append(current_batch)

    return batches

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(8))
def embed_batch(batch):
    """Call OpenAI embedding API with automatic retry."""
    return clientopenai.embeddings.create(
        model="text-embedding-3-large",
        input=batch
    )

def save_embeddings_to_disk(texts, embeddings, metadata_list, path="embeddings.jsonl"):
    with open(path, "a", encoding="utf-8") as f:
        for i in range(len(texts)):
            data = {
                "id": str(uuid.uuid4()),
                "text": texts[i],
                "embedding": embeddings[i],
                "metadata": metadata_list[i]
            }
            f.write(json.dumps(data) + "\n")

from tenacity import retry, wait_random_exponential, stop_after_attempt

@retry(wait=wait_random_exponential(min=1, max=30), stop=stop_after_attempt(5))
def safe_upsert(client, collection_name, points):
    """Handles transient upload issues with automatic retry."""
    client.upsert(collection_name=collection_name, points=points)

def get_embedding(docs):
    qdrant = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
            )
    print(f"Preparing documents")

    texts, metadatas = [], []
    for doc in docs:
        if hasattr(doc, "page_content") and isinstance(doc.page_content, str):
            chunks = chunk_text(doc.page_content)
            texts.extend(chunks)
            metadatas.extend([doc.metadata] * len(chunks))

    print(f"Found: {len(texts)} text chunks")

    saved = load_saved_embeddings()
    saved_ids = {s["id"] for s in saved}
    saved_texts = {s["text"] for s in saved}
    remaining = [(t, m) for t, m in zip(texts, metadatas) if t not in saved_texts]


    if not remaining:
        print("All chunks already embedded")
        upload_to_qdrant(saved, qdrant)
        return

    print(f"{len(remaining)} new chunks to embed")

    texts, metadatas = zip(*remaining)
    batches = safe_batches(texts)
    print(f"Created {len(batches)} safe batches")

    for i, batch in enumerate(batches, 1):
        print(f"Embedding batch {i}/{len(batches)} ({len(batch)} chunks)")
        try:
            response = embed_batch(batch)
            embeddings = [item.embedding for item in response.data]
            save_embeddings_to_disk(batch, embeddings, metadatas[:len(batch)])
            print(f"Saved: {len(batch)} embeddings")
            time.sleep(1)
        except Exception as e:
            print(f"Failed batch : {i} : {e}")
            continue

    print("Uploading saved embeddings to Qdrant")
    all_data = load_saved_embeddings()
    upload_to_qdrant(all_data, qdrant)
    print("Embedding pipeline complete")

def embed_query(text: str):
    response = clientopenai.embeddings.create(
        input=[text],
        model="text-embedding-3-large"
    )
    return response.data[0].embedding
