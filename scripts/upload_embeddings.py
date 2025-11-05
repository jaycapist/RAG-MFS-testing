import os
import json
import time
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from tenacity import retry, wait_random_exponential, stop_after_attempt

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "mfs_collection"
EMBEDDINGS_PATH = "embeddings.jsonl"

qdrant = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

collections = qdrant.get_collections().collections
if not any(c.name == COLLECTION_NAME for c in collections):
    print(f"🚧 Collection '{COLLECTION_NAME}' not found. Recreating...")
    qdrant.recreate_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=1536,
            distance=Distance.COSINE
        )
    )
else:
    print(f"Collection '{COLLECTION_NAME}' already exists.")

def load_saved_embeddings(path=EMBEDDINGS_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

@retry(wait=wait_random_exponential(min=1, max=30), stop=stop_after_attempt(5))
def safe_upsert(client, collection_name, points):
    """Handles transient upload issues with automatic retry."""
    client.upsert(collection_name=collection_name, points=points)


def upload_to_qdrant(data, qdrant, batch_size=100):
    print(f"Uploading {len(data)} embeddings to Qdrant")

    total = len(data)
    for i in range(0, total, batch_size):
        batch = data[i:i+batch_size]
        for item in batch:
            if len(item["embedding"]) != 1536:
                print(f"Bad vector length : {len(item['embedding'])} : {item['id']}")
        points = [
            PointStruct(
                id=item["id"],
                vector=item["embedding"],
                payload={
                    "text": item["text"],
                    **item.get("metadata", {})
                }
            )
            for item in batch
        ]

        try:
            safe_upsert(qdrant, COLLECTION_NAME, points)
            print(f"Uploaded batch {i//batch_size + 1}")
            time.sleep(0.5)
        except Exception as e:
            print(f"Failed to upload : {i//batch_size + 1} : {e}")


if __name__ == "__main__":
    print("Loading saved embeddings")
    data = load_saved_embeddings()

    print(f"Read {len(data)} embeddings")

    qdrant = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )

    print("Uploading to Qdrant")
    upload_to_qdrant(data, qdrant)
