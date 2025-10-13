from qdrant_client import QdrantClient
from qdrant_client.http.models import SearchParams
import os
from dotenv import load_dotenv
from scripts.get_embedding import embed_query

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "mfs_collection"

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def retrieve_top_k(query, k=5):
    query_vector = embed_query(query)

    search_result = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=k,
        with_payload=True,
        search_params=SearchParams(hnsw_ef=128)
    )
    return search_result

def format_context(results):
    return "\n\n".join(r.payload.get("text", "") for r in results)
