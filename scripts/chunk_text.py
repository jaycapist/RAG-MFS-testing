import re
from nltk.tokenize import sent_tokenize

def chunk_text(text, max_tokens=400, overlap=100):
    """
    Chunk using a sentence-based sliding window
    Fall back to paragraph chunking for longer documents

    Args:
        text (str): raw document text
        max_tokens (int): max number of words per chunk.
        overlap (int): number of words to overlap between chunks.

    Returns:
        List[str]: List of text chunks.
    """
    if not text.strip():
        return []

    # normalise spacing
    text = re.sub(r'\n{2,}', '\n\n', text.strip())

    # sentence tokenisation
    try:
        sentences = sent_tokenize(text)
    except LookupError:
        import nltk
        nltk.download("punkt")
        sentences = sent_tokenize(text)

    chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        token_count = len(sentence.split())
        if current_length + token_count > max_tokens:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            # Start with overlap
            current_chunk = current_chunk[-overlap:] if overlap else []
            current_length = sum(len(s.split()) for s in current_chunk)

        current_chunk.append(sentence)
        current_length += token_count

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
