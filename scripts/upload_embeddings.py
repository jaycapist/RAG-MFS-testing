import os
import json
import time
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from qdrant_client.http.exceptions import UnexpectedResponse
from tenacity import retry, wait_random_exponential, stop_after_attempt
from pathlib import Path

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "mfs_collection"
EMBEDDINGS_PATH = "embeddings.jsonl"
EMBEDDING_SIZE = 1024  # BGE-large


# Loads embeds from embeddings.jsonl
def load_saved_embeddings(path=EMBEDDINGS_PATH):
    path = Path(path)
    if not path.exists():
        print(f"File not found: {path.resolve()}")
        return []
    
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


# Check that `mfs_collection` exists
def collection_exists(client: QdrantClient, name: str) -> bool:
    try:
        client.get_collection(name)
        return True
    except UnexpectedResponse:
        return False
    except Exception:
        return False


# Safe Qdrant upload retry
@retry(wait=wait_random_exponential(min=1, max=30), stop=stop_after_attempt(5))
def safe_upsert(client, collection_name, points):
    client.upsert(
        collection_name=collection_name,
        points=points
    )


# Upload pipeline to Qdrant
def upload_to_qdrant(data, qdrant, batch_size=100):
    print(f"Prepping to upload {len(data)} embeddings")

    # If collection does not exist, create collection
    if not collection_exists(qdrant, COLLECTION_NAME):
        print(f"Collection '{COLLECTION_NAME}' not found. Creating...")

        qdrant.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=EMBEDDING_SIZE,
                distance=Distance.COSINE
            )
        )

    else:
        print(f"Collection '{COLLECTION_NAME}' already exists")

        # Retrieve existing dimension to validate
        info = qdrant.get_collection(COLLECTION_NAME)
        existing_dim = info.vectors.size

        # Recreate collection if 
        if existing_dim != EMBEDDING_SIZE:
            print(f"Dimensions mismatch: {existing_dim} - {EMBEDDING_SIZE}")
            print("Recreating collection")

            qdrant.recreate_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=EMBEDDING_SIZE,
                    distance=Distance.COSINE
                )
            )

    # Upload in batches
    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]

        points = [
            PointStruct(
                id=item["id"],
                vector=item["embedding"],
                payload={"text": item["text"], **item.get("metadata", {})}
            )
            for item in batch
            if len(item["embedding"]) == EMBEDDING_SIZE
        ]

        if not points:
            print(f"Skipping empty/invalid batch {i // batch_size + 1}")
            continue

        try:
            safe_upsert(qdrant, COLLECTION_NAME, points)
            print(f"Uploaded batch {i // batch_size + 1} ({len(points)} points)")
            time.sleep(0.2)
        except Exception as e:
            print(f"Failed batch : {i // batch_size + 1} : {e}")


# Main upload pipeline
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

    print("Uploading to Qdrant...")
    upload_to_qdrant(data, qdrant)
    print("Done!")
