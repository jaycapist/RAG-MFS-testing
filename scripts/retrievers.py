import os
import re
import numpy as np
from typing import List, Dict, Optional, Union
from collections import defaultdict
from dotenv import load_dotenv

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter, FieldCondition, MatchValue, ScoredPoint
)

from openai import OpenAI


load_dotenv()

# Qdrant config
COLLECTION_NAME = "mfs_collection" # VARIABLE
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# OpenAI config
client = OpenAI()
EMBED_MODEL = "text-embedding-3-large"

_rx_tok = re.compile(r"[A-Za-z0-9_]+")


# Helper functions
def toks(s: str):
    return [t.lower() for t in _rx_tok.findall(s or "")]


def minmax(xs):
    xs = np.asarray(xs, dtype=float)
    lo, hi = xs.min() if len(xs) else 0.0, xs.max() if len(xs) else 1.0
    return (xs - lo) / (hi - lo + 1e-9)


def group_by_doc(chunks: List[ScoredPoint]) -> Dict[str, List[ScoredPoint]]:
    groups = defaultdict(list)
    for r in chunks:
        fam = (
            r.payload.get("family_id") or
            r.payload.get("doc_id") or
            r.payload.get("url") or
            r.payload.get("title") or
            r.payload.get("source") or
            str(r.id)
        )
        groups[fam].append(r)
    return groups

# Calculate BM25 scores
def compute_bm25_scores(query, docs):
    from rank_bm25 import BM25Okapi

    corpus = []

    for d in docs:
        p = d.payload or {}

        committees = p.get("committee_codes", [])
        if isinstance(committees, list):
            committees = " ".join(committees)

        stances = p.get("stance", [])
        if isinstance(stances, list):
            stances = " ".join(stances)

        topics = p.get("topic", [])
        if isinstance(topics, list):
            topics = " ".join(topics)

        metas = p.get("meta", [])
        if isinstance(metas, list):
            metas = " ".join(metas)

        s = " ".join(filter(None, [
            p.get("source", ""),
            str(p.get("year", "")),
            p.get("month", ""),
            p.get("full_date", ""),
            committees,
            p.get("file_type", ""),
            p.get("body_code", ""),
            stances,
            topics,
            metas,
            p.get("text", "")
        ]))

        corpus.append(toks(s))

    bm25 = BM25Okapi(corpus)
    return bm25.get_scores(toks(query))



def build_filter(metadata):
    if not metadata:
        return None

    return Filter(
        must=[
            FieldCondition(
                key=k,
                match=MatchValue(value=v)
            ) for k, v in metadata.items()
        ]
    )


# Retriever logic
def retrieve(
    query: str,
    k: int = 10,
    alpha: float = 0.3,
    metadata: Optional[Dict[str, Union[str, int]]] = None,
    return_all_chunks: bool = False
):
    """
    Hybrid retriever:
      1. Metadata filter
      2. Group chunks
      3. Score docs
      4. Return: all chunks for each document
    """

    # Filter with metadata
    filt = build_filter(metadata)

    chunks, _ = qdrant.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter=filt,
        limit=10_000,
        with_payload=True,
        with_vectors=True
    )

    if not chunks:
        return []

    # Group chunks, get unique docs
    grouped = group_by_doc(chunks)

    doc_reps = []
    for lst in grouped.values():
        # pick the first chunk of the document as representative
        rep = min(lst, key=lambda r: r.payload.get("chunk_index", 0))
        doc_reps.append(rep)

    # Embed query
    query_vec = client.embeddings.create(
        model=EMBED_MODEL,
        input=query
    ).data[0].embedding
    q = np.array(query_vec)

    # Calculate vector similarity by doc
    vec_scores = []
    for rep in doc_reps:
        if rep.vector is None:
            vec_scores.append(0)
        else:
            v = np.array(rep.vector)
            sim = np.dot(v, q) / (np.linalg.norm(v) * np.linalg.norm(q) + 1e-9)
            vec_scores.append(float(sim))

    # BM25
    bm25_scores = compute_bm25_scores(query, doc_reps)

    # Normalize and do hybrid 
    bm25_n = minmax(bm25_scores)
    vec_n = minmax(vec_scores)
    rel = alpha * bm25_n + (1 - alpha) * vec_n

    # Rank docs
    order = np.argsort(-rel)
    top_docs = [doc_reps[i] for i in order[:k]]

    final = []
    for rep in top_docs:
        key = rep.payload.get("source") or rep.payload.get("doc_id")
        final.extend(grouped[key])
    return final

def format_context(results: List[ScoredPoint]) -> str:
    return "\n\n".join(r.payload.get("text", "") for r in results)
