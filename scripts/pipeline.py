from load_pdfs import load_pdfs
from get_embedding import get_embedding

docs = load_pdfs("data/")
print(f"Loaded {len(docs)} documents")
get_embedding(docs)
print("Pipeline complete")
