def print_sources(result, preview=140):
    print("\nSources:")
    seen = set()
    for d in result.get("context", []):
        src = d.metadata.get("source", "unknown")
        if src in seen: continue
        seen.add(src)
        page = d.metadata.get("page")
        snippet = d.page_content.replace("\n", " ")[:preview]
        print(f"- {src} (p.{page+1 if isinstance(page, int) else '?'}) :: {snippet}...")

def list_top_docs(query, retriever, k=10, preview=120):
    docs = retriever.get_relevant_documents(query)[:k]
    print(f"Top {len(docs)} results for: {query}")
    for i, d in enumerate(docs):
        src = d.metadata.get("source", "unknown")
        snippet = d.page_content.replace("\n", " ")[:preview]
        print(f"{i+1}. {src}: {snippet}...")