from retrievers import retrieve, format_context
from qa import answer_question
from printer import format_answer_with_sources_json
import json

# Test query
query = "tll me about CAB minutes in Fall 2020"

k = 15
alpha = 0.3

# Metadata testing
metadata_filter = {
    "file_type": "minutes",
    "committee_codes": "CAB",
    "semester": "Fall"
}

# retrieve docs
docs = retrieve(
    query=query,
    k=k,
    alpha=alpha,
    metadata=metadata_filter,
    return_all_chunks=True
)

# Inspect chunks
for doc in docs:
    print(f"Source: {doc.payload.get('source')}")
    print(doc.payload.get('text', '')[:300])
    print("-" * 50)

context = format_context(docs)
answer = answer_question(context, query)
result = format_answer_with_sources_json(answer, docs)
print(json.dumps(result, indent=2))
