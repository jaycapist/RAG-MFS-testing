import os
import random
from pathlib import Path
from scripts.pdf_extraction import extract_text_from_pdf
from scripts.get_embedding import embed_query
from scripts.retrievers import retrieve
from qdrant_client.http.models import SearchParams
from qdrant_client import QdrantClient
from dotenv import load_dotenv
import numpy as np

load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLL = "mfs_collection"
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def sample_query_from_text(text, n_words=8):
    words = text.split()
    if len(words) < n_words:
        return text
    start = random.randint(0, len(words) - n_words)
    return " ".join(words[start:start + n_words])

def test_random_pdf_retrieval(data_dir="data", n_samples=5):
    pdfs = list(Path(data_dir).rglob("*.pdf"))
    if not pdfs:
        print("No PDFs found")
        return

    print(f"Testing {n_samples} random PDFs\n")

    random.shuffle(pdfs)
    tested = 0

    for pdf_path in pdfs:
        if tested >= n_samples:
            break

        text, pages, used_ocr = extract_text_from_pdf(str(pdf_path))
        if not text.strip():
            continue

        query = sample_query_from_text(text)
        print(f"\nOriginal File: {pdf_path.name}")
        print(f"Sampled Query: '{query}'")
        print(f"Used OCR: {'Yes' if used_ocr else 'No'}")

        results = retrieve(query, k=5)
        found = False
        print("\nRetrieved Documents:")
        for r in results:
            source = r.payload.get("source", "unknown")
            snippet = r.payload.get("text", "").replace("\n", " ")[:160]
            print(f"- {source} :: {snippet}...")

            if source == pdf_path.name:
                found = True

        print(f"\nMatch Found: {'Yes' if found else 'No'}")
        print("-" * 50)

        tested += 1

if __name__ == "__main__":
    test_random_pdf_retrieval("data", n_samples=5)
