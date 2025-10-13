from scripts.load_pdfs import load_docs
from scripts.helpers import add_year_metadata_consistent
from scripts.get_embedding import get_embeddings
from qdrant_client import QdrantClient

docs = load_docs("data")
print(f"Loaded {len(docs)} documents.")

add_year_metadata_consistent(docs)

get_embeddings(docs)
print("Embedding + Qdrant upload complete.")
