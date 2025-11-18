from scripts.retrievers import retrieve, format_context
from scripts.qa import answer_question, format_answer_with_sources

query = "What are the recommendations in the CAPP 2024 report?"

docs = retrieve(query)

context = format_context(docs)

answer = answer_question(context, query)

format_answer_with_sources(answer, docs)
