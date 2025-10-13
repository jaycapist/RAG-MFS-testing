import os
import json
import time
from tqdm import tqdm
from tenacity import retry, wait_random_exponential, stop_after_attempt
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct
from scripts.chunk_text import chunk_text
import tiktoken

# --- Load env ---
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

clientopenai = OpenAI(api_key=OPENAI_API_KEY)
tokenizer = tiktoken.encoding_for_model("text-embedding-3-small")

MAX_TOKENS = 200_000
MAX_CHUNK_TOKENS = 10_000
BATCH_FILE = "embeddings.jsonl"
COLLECTION_NAME = "mfs_collection"

# --- Token helpers ---
def num_tokens(text):
    return len(tokenizer.encode(text))

def safe_batches(texts):
    """Yield batches that respect token and size limits."""
    batches, current_batch, current_tokens = [], [], 0
    for text in texts:
        tokens = num_tokens(text)
        if tokens > MAX_CHUNK_TOKENS:
            print(f"⚠️ Skipping oversized chunk ({tokens} tokens)")
            continue
        if current_tokens + tokens > MAX_TOKENS:
            batches.append(current_batch)
            current_batch, current_tokens = [text], tokens
        else:
            current_batch.append(text)
            current_tokens += tokens
    if current_batch:
        batches.append(current_batch)
    return batches

# --- Safe embedding request with retry ---
@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(8))
def embed_batch(batch):
    """Call OpenAI embedding API with automatic retry."""
    return clientopenai.embeddings.create(
        model="text-embedding-3-small",
        input=batch
    )

# --- Save progress to disk ---
def save_embeddings_to_disk(texts, embeddings, metadata_list, path=BATCH_FILE):
    with open(path, "a", encoding="utf-8") as f:
        for i in range(len(texts)):
            data = {
                "id": hash(texts[i]),
                "text": texts[i],
                "embedding": embeddings[i],
                "metadata": metadata_list[i]
            }
            f.write(json.dumps(data) + "\n")

# --- Load saved embeddings ---
def load_saved_embeddings(path=BATCH_FILE):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

# --- Upload to Qdrant ---
def upload_to_qdrant(data, qdrant):
    points = [
        PointStruct(
            id=item["id"],
            vector=item["embedding"],
            payload={"text": item["text"], **item.get("metadata", {})}
        )
        for item in data
    ]
    qdrant.upload_collection(collection_name=COLLECTION_NAME, points=points)
    print(f"✅ Uploaded {len(points)} points to Qdrant")

# --- Main embedding pipeline ---
def get_embedding(docs):
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    print(f"🔍 Preparing documents...")

    texts, metadatas = [], []
    for doc in docs:
        if hasattr(doc, "page_content") and isinstance(doc.page_content, str):
            chunks = chunk_text(doc.page_content)
            texts.extend(chunks)
            metadatas.extend([doc.metadata] * len(chunks))

    print(f"🧠 Found {len(texts)} text chunks total.")

    # ✅ Skip already embedded ones
    saved = load_saved_embeddings()
    saved_ids = {s["id"] for s in saved}
    remaining = [(t, m) for t, m in zip(texts, metadatas) if hash(t) not in saved_ids]

    if not remaining:
        print("✅ All chunks already embedded.")
        upload_to_qdrant(saved, qdrant)
        return

    print(f"⏩ {len(remaining)} new chunks to embed.")

    texts, metadatas = zip(*remaining)
    batches = safe_batches(texts)
    print(f"📦 Created {len(batches)} safe batches.")

    for i, batch in enumerate(batches, 1):
        print(f"🔄 Embedding batch {i}/{len(batches)} ({len(batch)} chunks)...")
        try:
            response = embed_batch(batch)
            embeddings = [item.embedding for item in response.data]
            save_embeddings_to_disk(batch, embeddings, metadatas[:len(batch)])
            print(f"✅ Saved {len(batch)} embeddings to disk.")
            time.sleep(1)  # polite spacing between batches
        except Exception as e:
            print(f"❌ Failed batch {i}: {e}")
            continue

    print("🚀 Uploading all saved embeddings to Qdrant...")
    all_data = load_saved_embeddings()
    upload_to_qdrant(all_data, qdrant)
    print("🎉 Embedding pipeline complete.")

def embed_query(text: str):
    from openai import OpenAI
    import os
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    response = client.embeddings.create(
        input=[text],
        model="text-embedding-3-small"
    )
    return response.data[0].embedding
