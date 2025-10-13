# scripts/upload_only.py
from qdrant_client import QdrantClient
from get_embedding import load_saved_embeddings, upload_to_qdrant
import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
data = load_saved_embeddings()

print(f"📦 Loaded {len(data)} saved embeddings from disk")
upload_to_qdrant(data, qdrant, batch_size=100)
