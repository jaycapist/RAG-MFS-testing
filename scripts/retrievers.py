from qdrant_client import QdrantClient
from qdrant_client.http.models import SearchParams
import os
from dotenv import load_dotenv
from get_embedding import embed_query
from rank_bm25 import BM25Okapi

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "mfs_collection"

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

def retrieve(query, k=5, alpha=0.5, use_mmr=False, lambda_param=0.5):
    query_vector = embed_query(query)

    search_results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=50,
        with_payload=True,
        with_vectors=True,
        search_params=SearchParams(hnsw_ef=128)
    )

    if not search_results:
        return []

    hybrid_results = hybrid_rerank(query, search_results, alpha=alpha)

    if use_mmr:
        doc_vectors = [np.array(doc.vector) for doc in hybrid_results]
        mmr_results = mmr(
            query_vec=np.array(query_vector),
            doc_vecs=doc_vectors,
            docs=hybrid_results,
            lambda_param=lambda_param,
            top_k=k
        )
        return mmr_results

    return hybrid_results[:k]

def format_context(results):
    return "\n\n".join(r.payload.get("text", "") for r in results)

def compute_bm25_scores(query, docs):
    tokenized_corpus = [doc.payload["text"].split() for doc in docs]
    bm25 = BM25Okapi(tokenized_corpus)
    query_tokens = query.split()
    return bm25.get_scores(query_tokens)


def hybrid_rerank(query, results, alpha=0.5):
    bm25_scores = compute_bm25_scores(query, results)
    combined = []

    for i, doc in enumerate(results):
        vector_score = doc.score
        bm25_score = bm25_scores[i]
        combined_score = alpha * bm25_score + (1 - alpha) * vector_score
        combined.append((combined_score, doc))

    combined.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in combined[:5]]

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def mmr(query_vec, doc_vecs, docs, lambda_param=0.5, top_k=5):
    selected = []
    candidates = list(range(len(docs)))
    doc_vecs = np.array(doc_vecs)

    while len(selected) < top_k:
        mmr_scores = []
        for i in candidates:
            sim_to_query = cosine_similarity([query_vec], [doc_vecs[i]])[0][0]
            sim_to_selected = max(
                [cosine_similarity([doc_vecs[i]], [doc_vecs[j]])[0][0] for j in selected]
            ) if selected else 0
            score = lambda_param * sim_to_query - (1 - lambda_param) * sim_to_selected
            mmr_scores.append((score, i))

        mmr_scores.sort(reverse=True)
        selected_idx = mmr_scores[0][1]
        selected.append(selected_idx)
        candidates.remove(selected_idx)

    return [docs[i] for i in selected]
