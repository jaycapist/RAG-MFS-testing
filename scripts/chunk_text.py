def chunk_text(text, max_tokens=500):
    words = text.split()
    return [
        " ".join(words[i:i + max_tokens])
        for i in range(0, len(words), max_tokens)
    ]
