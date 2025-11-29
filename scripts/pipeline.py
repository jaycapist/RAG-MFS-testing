from scripts.load_pdfs import load_pdfs
from scripts.get_embedding import get_embedding

docs = load_pdfs("data/") # VARIABLE
print(f"Loaded {len(docs)} documents")
for doc in docs[:100]:
    print(f"{doc.metadata.get('source')} > {doc.metadata}")
get_embedding(docs)
print("Pipeline complete")
