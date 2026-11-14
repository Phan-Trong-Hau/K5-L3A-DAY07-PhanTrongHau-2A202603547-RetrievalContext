"""Five retrieval methods over the same Day 6 corpus; no gold input."""
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

from .common import load, sha256


def tokenize(text):
    return re.findall(r'\w+', unicodedata.normalize('NFC', text).casefold())


def matches(chunk, filters):
    return all(chunk['metadata'].get(key) == value for key, value in (filters or {}).items())


class BM25:
    def __init__(self, chunks, k1=1.5, b=0.75):
        self.chunks, self.k1, self.b = chunks, k1, b
        self.counts = [Counter(tokenize(c['text'])) for c in chunks]
        self.lengths = [sum(c.values()) for c in self.counts]
        self.average = sum(self.lengths) / len(chunks)
        df = Counter(t for row in self.counts for t in row)
        self.idf = {t: math.log(1 + (len(chunks) - n + .5) / (n + .5)) for t, n in df.items()}

    def search(self, query, *, filters=None, top_k=3):
        terms = set(tokenize(query))
        rows = []
        for c, counts, length in zip(self.chunks, self.counts, self.lengths):
            if not matches(c, filters):
                continue
            score = sum(self.idf.get(t, 0) * counts[t] * (self.k1 + 1) /
                        (counts[t] + self.k1 * (1 - self.b + self.b * length / self.average)) for t in terms)
            if score > 0:
                rows.append({**c, 'score': score, 'method': 'bm25'})
        return sorted(rows, key=lambda r: (-r['score'], r['id']))[:top_k]


def rrf(rankings, top_k, constant=60):
    scores, rows, ranks = Counter(), {}, {}
    for name, ranking in rankings.items():
        for rank, row in enumerate(ranking, 1):
            cid = row['id']
            rows[cid] = row
            scores[cid] += 1 / (constant + rank)
            ranks.setdefault(cid, {})[name] = rank
    return [{**rows[cid], 'score': scores[cid], 'method': 'hybrid', 'component_ranks': ranks[cid]}
            for cid in sorted(scores, key=lambda cid: (-scores[cid], cid))[:top_k]]


def mmr(ranking, vectors, top_k, weight=.75):
    """Maximize query relevance minus similarity to already selected documents."""
    if not 0 < weight <= 1:
        raise ValueError('MMR weight must be in (0, 1]')
    normalized = {}
    for row in ranking:
        vector = vectors[row['id']]
        norm = math.sqrt(sum(x*x for x in vector))
        if not norm:
            raise ValueError('Zero document vector')
        normalized[row['id']] = [x/norm for x in vector]
    selected, remaining = [], list(ranking)
    while remaining and len(selected) < top_k:
        def score(row):
            redundancy = max((sum(x*y for x, y in zip(normalized[row['id']], normalized[s['id']]))
                              for s in selected), default=0)
            return weight * row['score'] - (1-weight) * redundancy
        best = min(remaining, key=lambda row: (-score(row), row['id']))
        selected.append({**best, 'dense_score': best['score'], 'score': score(best), 'method': 'mmr'})
        remaining.remove(best)
    return selected


class Retriever:
    def __init__(self, data='data/day6', store='.qdrant', collection='day7'):
        from fastembed import TextEmbedding
        from qdrant_client import QdrantClient, models
        self.models, self.collection = models, collection
        data = Path(data)
        provenance = load(data / 'provenance.json')
        for name, expected in provenance['sha256'].items():
            if sha256(data / name) != expected:
                raise ValueError(f'Day 6 snapshot checksum mismatch: {name}')
        self.chunks = load(data / 'chunks.json')
        vectors = load(data / 'vectors.json')
        self.vector_by_id = {v['id']: v['vector'] for v in vectors}
        self.reranker = None
        self.rerank_cache = {}
        if len(vectors) != len(self.chunks) or [v['id'] for v in vectors] != [c['id'] for c in self.chunks]:
            raise ValueError('Day 6 vector/chunk ID mismatch')
        self.dimensions = provenance['dimensions']
        if any(len(v['vector']) != self.dimensions for v in vectors):
            raise ValueError('Day 6 vector dimension mismatch')
        self.embedder = TextEmbedding(model_name=provenance['embedding_model'], threads=4, lazy_load=True)
        # Pin the actual tokenizer/ONNX bytes, not merely the displayed model name.
        model_dir = Path(self.embedder.model._model_dir)
        for name, expected in load(data / 'embedding.json')['files'].items():
            if sha256(model_dir / name) != expected:
                raise ValueError(f'Embedding snapshot mismatch: {name}')
        self.client = QdrantClient(path=str(store))
        try:
            # Immutable exported vectors; no re-embedding or random-vector fallback.
            if self.client.collection_exists(collection):
                self.client.delete_collection(collection)
            self.client.create_collection(collection, vectors_config=models.VectorParams(
                size=self.dimensions, distance=models.Distance.COSINE))
            for start in range(0, len(vectors), 128):
                self.client.upsert(collection, points=[models.PointStruct(
                    id=v['point_id'], vector=v['vector'], payload=c)
                    for c, v in zip(self.chunks[start:start+128], vectors[start:start+128])])
        except Exception:
            self.client.close()
            raise
        self.lexical = BM25(self.chunks)
        self.query_cache = {}

    def search(self, query, *, filters=None, top_k=3, method='dense', candidates=20):
        if not isinstance(query, str) or not query.strip() or top_k < 1 or candidates < 1:
            raise ValueError('Invalid query/top_k/candidates')
        if set(filters or {}) - {'chapter', 'language'}:
            raise ValueError('Only explicit chapter/language filters are supported')
        if method == 'bm25':
            rows = self.lexical.search(query, filters=filters, top_k=top_k)
        elif method == 'dense':
            if query not in self.query_cache:
                v = next(self.embedder.query_embed(query)).tolist()
                if len(v) != self.dimensions:
                    raise ValueError('Query embedding dimension mismatch')
                self.query_cache[query] = v
            filt = self.models.Filter(must=[self.models.FieldCondition(
                key=f'metadata.{k}', match=self.models.MatchValue(value=v)) for k, v in filters.items()]) if filters else None
            points = self.client.query_points(self.collection, query=self.query_cache[query],
                limit=top_k, query_filter=filt).points
            rows = [{**p.payload, 'score': p.score, 'method': 'dense'} for p in points]
        elif method == 'hybrid':
            rows = rrf({name: self.search(query, filters=filters, top_k=candidates, method=name)
                        for name in ('dense', 'bm25')}, top_k)
        elif method == 'mmr':
            rows = mmr(self.search(query, filters=filters, top_k=candidates, method='dense'),
                       self.vector_by_id, top_k)
        elif method == 'rerank':
            candidates_rows = self.search(query, filters=filters, top_k=candidates,
                                          method='hybrid', candidates=candidates)
            key = (query, tuple(r['id'] for r in candidates_rows))
            if key not in self.rerank_cache:
                if self.reranker is None:
                    from fastembed.rerank.cross_encoder import TextCrossEncoder
                    self.reranker = TextCrossEncoder('Xenova/ms-marco-MiniLM-L-6-v2', threads=4)
                scores = list(self.reranker.rerank(query, [r['text'] for r in candidates_rows], batch_size=16))
                if len(scores) != len(candidates_rows) or any(not math.isfinite(float(s)) for s in scores):
                    raise ValueError('Invalid cross-encoder scores')
                self.rerank_cache[key] = scores
            rows = sorted([{**r, 'fusion_score': r['score'], 'score': float(s), 'method': 'rerank',
                            'reranker': 'Xenova/ms-marco-MiniLM-L-6-v2'}
                           for r, s in zip(candidates_rows, self.rerank_cache[key])],
                          key=lambda r: (-r['score'], r['id']))[:top_k]
        else:
            raise ValueError(f'Unknown retrieval method: {method}')
        return [{**r, 'rank': i} for i, r in enumerate(rows, 1)]

    def close(self):
        self.client.close()
