import os
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
import argparse

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLL = "mfs_collection"

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def get_pdf_filenames(data_dir="data"):
    data_dir = Path(data_dir)
    return [f.name for f in data_dir.rglob("*.pdf")]

def check_indexed_chunks(filenames, preview=100):
    total_found = 0
    total_missing = 0

    print(f"\nScanning {len(filenames)} PDFs for chunks\n")

    for name in filenames:
        result = client.scroll(
            collection_name=COLL,
            scroll_filter=Filter(
                must=[FieldCondition(key="source", match=MatchValue(value=name))]
            ),
            limit=1000,
            with_payload=True
        )
        points = result[0]
        if not points:
            print(f"MISSING: {name}")
            total_missing += 1
        else:
            print(f"{name} — {len(points)} chunks")
            for i, pt in enumerate(points[:3]):
                text = pt.payload.get("text", "").strip().replace("\n", " ")
                snippet = text[:preview]
                print(f"   - Chunk {i+1}: {snippet}...")
            total_found += 1

    print(f"\nFound chunks: {total_found} files")
    print(f"Missing chunks: {total_missing} files\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="data", help="Directory with PDFs")
    args = parser.parse_args()

    filenames = get_pdf_filenames(args.data_dir)
    check_indexed_chunks(filenames)
