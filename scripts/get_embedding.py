import os
from tqdm import tqdm
from dotenv import load_dotenv

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from openai import OpenAI

from scripts.chunk_text import chunk_text
import tiktoken

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
clientopenai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
tokenizer = tiktoken.encoding_for_model("text-embedding-3-small")
MAX_TOKENS = 200_000
MAX_CHUNK_TOKENS = 10_000

def num_tokens(text):
    return len(tokenizer.encode(text))


def safe_batches(texts):
    """Yield batches that respect token and size limits."""
    batches = []
    current_batch = []
    current_tokens = 0

    for text in texts:
        tokens = num_tokens(text)

        if tokens > MAX_CHUNK_TOKENS:
            print(f"Skipping oversized chunk: ({tokens} tokens)")
            continue

        if current_tokens + tokens > MAX_TOKENS:
            batches.append(current_batch)
            current_batch = [text]
            current_tokens = tokens
        else:
            current_batch.append(text)
            current_tokens += tokens

    if current_batch:
        batches.append(current_batch)

    return batches


def get_embedding(docs):
    qdrant = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
    )
    texts = []
    metadatas = []

    for doc in docs:
        if isinstance(doc.page_content, str):
            chunks = chunk_text(doc.page_content)
            texts.extend(chunks)
            metadatas.extend([doc.metadata] * len(chunks))

    print(f"Embedding: {len(texts)} chunks")

    if not texts:
        print("Text chunks found to embed")
        return

    # Build safe batches
    batches = safe_batches(texts)
    print(f"Created {len(batches)} batches")

    vectors = []

    for i, batch in enumerate(batches):
        token_count = sum(num_tokens(t) for t in batch)
        print(f"Embedding batch {i + 1}/{len(batches)} ({len(batch)} chunks, {token_count} tokens)")

        response = clientopenai.embeddings.create(
            input=batch,
            model="text-embedding-3-small"
        )
        batch_vectors = [item.embedding for item in response.data]
        vectors.extend(batch_vectors)

    points = [
        PointStruct(
            id=i,
            vector=vectors[i],
            payload=metadatas[i]
        ) for i in range(len(vectors))
    ]

    qdrant.upload_collection(
        collection_name="mfs_collection",
        points=points
    )

    print("Uploaded embeddings to Qdrant")
def embed_query(text: str):
    from openai import OpenAI
    import os
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    response = client.embeddings.create(
        input=[text],
        model="text-embedding-3-small"
    )
    return response.data[0].embedding
