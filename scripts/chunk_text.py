import re
import tiktoken

encoding = tiktoken.encoding_for_model("text-embedding-3-large")
MAX_EMBEDDING_TOKENS = 8191

def count_tokens(text):
    return len(encoding.encode(text))

def chunk_text(text, max_tokens=2000, overlap=200):
    """
    True token-based chunker for OpenAI embeddings.
    Ensures no chunk ever exceeds model token limits.
    """

    if not text.strip():
        return []

    # Normalise spacing a bit
    text = re.sub(r"\s+", " ", text).strip()

    tokens = encoding.encode(text)
    chunks = []

    start = 0
    end = min(len(tokens), max_tokens)

    while start < len(tokens):
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)

        # Move to next window
        start = end - overlap
        if start < 0:
            start = 0

        end = start + max_tokens

    return chunks

def truncate_guard(text):
    tokens = encoding.encode(text)
    if len(tokens) > MAX_EMBEDDING_TOKENS:
        print(f"Truncating long chunk ({len(tokens)} tokens)")
        return encoding.decode(tokens[:MAX_EMBEDDING_TOKENS])
    return text
