from pathlib import Path
from scripts.load_pdfs import load_pdfs
from scripts.get_embedding import get_embedding, load_saved_embeddings
import json

TEST_DATA_DIR = "data/test/"

def inspect_sample_embeddings(path="embeddings.jsonl", max_docs=3):
    if not Path(path).exists():
        print("No embeddings file")
        return

    print(f"\nInspecting up to {max_docs} embeddings\n")
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= max_docs:
                break
            record = json.loads(line)
            print(f"Embedding {i+1}:")
            print(f"Text snippet: {record['text'][:100]}")
            print(f"Metadata: {record.get('metadata')}")
            print("-" * 60)

if __name__ == "__main__":
    print("Loading PDFs")
    docs = load_pdfs(TEST_DATA_DIR)
    print(f"Loaded {len(docs)} documents\n")

    for i, doc in enumerate(docs[:3]):
        print(f"Document {i+1}:")
        print(f"Metadata: {doc.metadata}")
        print(f"Content Preview: {doc.page_content[:100]}...\n")

    print("Running pipeline")
    get_embedding(docs)

    print("Embedding complete")

    inspect_sample_embeddings()