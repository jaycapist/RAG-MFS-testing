from langchain.chains import RetrievalQA
from helpers import parse_year_window

def ask_with_retriever(question, llm, retriever):
    chain = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff", retriever=retriever, return_source_documents=True
    )
    return chain.invoke({"query": question})

def ask_smart(question, llm, db, bm25, hybrid):
    y_min, y_max = parse_year_window(question)
    if y_min is not None:
        return ask_with_retriever(question, llm, db.as_retriever(search_kwargs={"k": 10, "filter": {"year": y_min}}))
    return ask_with_retriever(question, llm, hybrid)