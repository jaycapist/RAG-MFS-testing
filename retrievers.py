from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain.schema import Document
from helpers import parse_year_window

RETRIEVAL_MODE = "auto"
K = 10
MMR_K = 10
MMR_FETCH_K = 40
MMR_LAMBDA = 0.5
YEAR_FILTER_ENABLED = True

def build_retrievers(db, split_docs):
    bm25 = BM25Retriever.from_documents(
        [Document(page_content=d.page_content, metadata=d.metadata) for d in split_docs]
    )
    bm25.k = 10
    print("BM25 built")
    vec_retriever = db.as_retriever(search_kwargs={"k": 10})
    print("Vector store retriever built")
    hybrid = EnsembleRetriever(retrievers=[bm25, vec_retriever], weights=[0.5, 0.5])
    print("Hybrid retriever built")
    return bm25, vec_retriever, hybrid

def get_retriever_for_query(query, db, bm25, hybrid):
    if YEAR_FILTER_ENABLED:
        y_min, y_max = parse_year_window(query)
        if y_min:
            return db.as_retriever(search_kwargs={"k": K, "filter": {"year": y_min}})
    return hybrid