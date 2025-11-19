from scripts.retrievers import retrieve, format_context
from scripts.qa import answer_question, format_answer_with_sources

query = "insert query"

docs = retrieve("insert query", k=5)
for doc in docs:
    print(doc.payload.get("source"))
    print(doc.payload.get("text")[:300])
    print("-" * 50)


context = format_context(docs)

answer = answer_question(context, query)

format_answer_with_sources(answer, docs)
