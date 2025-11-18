import os
import json
import time
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from tenacity import retry, wait_random_exponential, stop_after_attempt
from pathlib import Path

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "mfs_collection"
EMBEDDINGS_PATH = "embeddings.jsonl"
EMBEDDING_SIZE = 3072  # text-embedding-3-large

def load_saved_embeddings(path=EMBEDDINGS_PATH):
    path = Path(path)
    if not path.exists():
        print(f"File not found: {path.resolve()}")
        return []
    
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

@retry(wait=wait_random_exponential(min=1, max=30), stop=stop_after_attempt(5))
def safe_upsert(client, collection_name, points):
    client.upsert(collection_name=collection_name, points=points)

def upload_to_qdrant(data, qdrant, batch_size=100):
    print(f"Prepping to upload {len(data)} embeddings")

    # Ensure collection exists
    if not qdrant.collection_exists(COLLECTION_NAME):
        print(f"Collection '{COLLECTION_NAME}' not found \nCreating '{COLLECTION_NAME}'")
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_SIZE,
                distance=Distance.COSINE
            )
        )
    else:
        print(f"Collection '{COLLECTION_NAME}' already exists")

    # Upload in batches
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]

        # Check embedding lengths
        for item in batch:
            if len(item["embedding"]) != EMBEDDING_SIZE:
                print(f"Skipping bad vector size:  ({len(item['embedding'])}): {item['id']}")
                continue

        points = [
            PointStruct(
                id=item["id"],
                vector=item["embedding"],
                payload={"text": item["text"], **item.get("metadata", {})}
            )
            for item in batch
            if len(item["embedding"]) == EMBEDDING_SIZE
        ]

        try:
            safe_upsert(qdrant, COLLECTION_NAME, points)
            print(f"Uploaded batch: {i // batch_size + 1}")
            time.sleep(0.5)
        except Exception as e:
            print(f"Failed batch : {i // batch_size + 1} : {e}")

if __name__ == "__main__":
    print("Loading saved embeddings...")
    data = load_saved_embeddings()

    print(f"Found {len(data)} embeddings")

    if not data:
        print("No embeddings to upload")
        exit()

    qdrant = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )

    print("Uploading")
    upload_to_qdrant(data, qdrant)
