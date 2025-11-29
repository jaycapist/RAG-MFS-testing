import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION = "mfs_collection" # VARIABLE

qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


def ensure_index(field_name: str, schema_type: str):
    """If missing index, create. Skip if exit."""
    try:
        print(f"Creating index: {field_name}")
        qdrant.create_payload_index(
            collection_name=COLLECTION,
            field_name=field_name,
            field_schema=schema_type,   # STRING, NOT DICT
        )
        print(f"✔ Index created for {field_name}")
    except Exception as e:
        msg = str(e).lower()
        if "already exists" in msg or "exists in" in msg:
            print(f"This index already exists: {field_name}")
        else:
            print(f"Failed to create an index : {field_name} : {e}")


if __name__ == "__main__":
    print(f"\nConnecting to collection: {COLLECTION}\n")

    # Main
    ensure_index("file_type", "keyword")
    ensure_index("year", "integer")
    ensure_index("committee_codes", "keyword")
    ensure_index("body_code", "keyword")

    # Date
    ensure_index("full_date", "keyword")
    ensure_index("year", "integer")
    ensure_index("semester", "keyword")
    ensure_index("month", "keyword")

    # Extra
    ensure_index("stance", "keyword")
    ensure_index("topic", "keyword")
    ensure_index("meta", "keyword")
    ensure_index("status", "keyword")
    ensure_index("action_type", "keyword")
    print("\nDone.\n")

    print("Current payload schema:\n")
    info = qdrant.get_collection(COLLECTION)
    print(info.payload_schema)
