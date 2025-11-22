from qdrant_client import QdrantClient
from qdrant_client.http.models import SearchParams
import os
import re
from dotenv import load_dotenv
from scripts.get_embedding import embed_query
from rank_bm25 import BM25Okapi
from collections import defaultdict
import numpy as np
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLL = "mfs_collection_test"
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

_rx_tok = re.compile(r"[A-Za-z0-9_]+")

def toks(s: str):
    return [t.lower() for t in _rx_tok.findall(s or "")]

def zscore(xs):
    xs = np.asarray(xs, dtype=float)
    mu, sd = xs.mean() if len(xs) else 0.0, xs.std() if len(xs) else 1.0
    return (xs - mu) / (sd if sd > 1e-9 else 1.0)

def minmax(xs):
    xs = np.asarray(xs, dtype=float)
    lo, hi = xs.min() if len(xs) else 0.0, xs.max() if len(xs) else 1.0
    return (xs - lo) / (hi - lo + 1e-9)

def year_in(q): 
    m = re.search(r"\b(19|20)\d{2}\b", q)
    return int(m.group()) if m else None

def intent_priors(query, item):
    q = query.lower()
    p = item.payload or {}
    doctype = (p.get("doctype") or "").lower()
    is_draft = bool(p.get("is_draft"))
    committee = (p.get("committee") or "").lower()
    title = (p.get("title") or "").lower()
    date_str = p.get("date")
    months_decay = 0.0
    if date_str:
        dt = datetime.fromisoformat(date_str)
        months = max(0, (datetime.utcnow() - dt).days / 30.44)
        months_decay = 0.5 ** (months / 18.0)

    boost = 0.0
    if "final report" in q and doctype == "report": boost += 1.0
    if "minutes" in q and doctype == "minutes": boost += 1.0
    if "resolution" in q and doctype == "resolution": boost += 1.0
    if "draft" not in q and is_draft: boost -= 0.5
    for tag in ["capp","sec","see","mfs"]:
        if tag in q and tag == committee:
            boost += 0.5
    y = year_in(q)
    if y and (str(y) in title or (p.get("session") or "").find(str(y)) != -1):
        boost += 0.3
    boost += 0.2 * months_decay
    return boost

# BM25
def compute_bm25_scores(query, docs):
    corpus = []
    for d in docs:
        p = d.payload or {}
        s = " ".join(filter(None, [
            p.get("title",""),
            p.get("committee",""),
            p.get("doctype",""),
            p.get("date",""),
            p.get("snippet",""),
            p.get("text","")
        ]))
        corpus.append(toks(s))
    bm25 = BM25Okapi(corpus)
    return bm25.get_scores(toks(query))

# group chunks
def group_by_doc(results):
    groups = defaultdict(list)
    for r in results:
        fam = r.payload.get("family_id") or r.payload.get("doc_id") or r.payload.get("url") or r.payload.get("title")
        groups[fam].append(r)
    return groups

# main retrieve
def retrieve(query, k=5, alpha=0.5, use_mmr=False, lambda_param=None, prefetch=300):
    qvec = embed_query(query)

    hits = client.search(
        collection_name=COLL,
        query_vector=qvec,
        limit=prefetch,
        with_payload=True,
        with_vectors=True,
        search_params=SearchParams(hnsw_ef=512)
    )
    if not hits: return []

    # 1) group chunks
    groups = group_by_doc(hits)
    # choose best chunk
    doc_reps = [max(rs, key=lambda r: r.score) for rs in groups.values()]
    # 2) hybrid relevance
    bm25 = compute_bm25_scores(query, doc_reps)
    bm25_n = minmax(bm25)
    vec = np.array([r.score for r in doc_reps], dtype=float)
    vec_n = minmax(vec)
    pri = np.array([intent_priors(query, r) for r in doc_reps], dtype=float)
    pri_n = minmax(pri)

    rel = alpha * bm25_n + (1 - alpha) * vec_n + 0.1 * pri_n

    # doc-level vectors diversity
    doc_vecs = np.vstack([np.array(r.vector) for r in doc_reps if r.vector is not None])
    # dynamic lambda: specific queries -> less diversity
    if lambda_param is None:
        specificity = 0
        specificity += 1 if year_in(query) else 0
        for tag in ["minutes","resolution","report","capp","sec","see","mfs"]:
            if tag in query.lower(): specificity += 1
        lambda_param = 0.2 - 0.03 * min(specificity, 3)

    # 3) MMR
    if use_mmr:
        selected = []
        cand = list(range(len(doc_reps)))
        rel_list = rel.tolist()
        while len(selected) < min(k, len(cand)):
            best_i, best_score = None, -1e9
            for i in cand:
                if selected:
                    sim_to_sel = max(cosine_similarity([doc_vecs[i]], [doc_vecs[j]])[0][0] for j in selected)
                else:
                    sim_to_sel = 0.0
                score = (lambda_param * rel_list[i]) - ((1 - lambda_param) * sim_to_sel)
                if score > best_score:
                    best_score, best_i = score, i
            selected.append(best_i)
            cand.remove(best_i)
        ranked = [doc_reps[i] for i in selected]
    else:
        order = np.argsort(-rel)
        ranked = [doc_reps[i] for i in order[:k]]

    return ranked

def format_context(results):
    return "\n\n".join(r.payload.get("text","") for r in results)