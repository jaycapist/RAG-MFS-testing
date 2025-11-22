def format_answer_with_sources(answer: str, docs, preview=150):
    print("\nResponse:")
    print(answer.strip())
    
    print("\nList of documents used:")
    seen = set()
    for d in docs:
        src = d.payload.get("source", "unknown")
        
        if src in seen:
            continue
        seen.add(src)

        link = d.payload.get("link", "<no link>")
        snippet = d.payload.get("text", "").replace("\n", " ").strip()[:preview]

        if not snippet:
            snippet = "(No visible content)"
        
        print(f"{src} {link}  # {snippet}...")