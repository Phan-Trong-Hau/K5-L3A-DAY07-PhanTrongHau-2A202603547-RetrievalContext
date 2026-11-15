#!/usr/bin/env python3
"""Exploratory agent with BM25, CLIP region retrieval, and on-demand vision.

Images stay in temporary storage. Vision descriptions are unverified; output
must be checked against the source PDF before being treated as evidence.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.bonus_pilot import PageRetriever
from scripts.describe_vietnam2035 import describe
from src.agent import Ollama
from src.agent_v2 import run_agent


class VisualRetriever(PageRetriever):
    def __init__(self, pdf, index, descriptions, vision_model, vision_limit):
        super().__init__(descriptions)
        self.pdf, self.vision_model, self.vision_limit = pdf, vision_model, vision_limit
        manifest = json.loads((index / 'manifest.json').read_text(encoding='utf-8'))
        if hashlib.sha256(pdf.read_bytes()).hexdigest() != manifest['source_sha256']:
            raise ValueError('PDF checksum does not match the visual index')
        self.embedder = TextEmbedding(model_name='Qdrant/clip-ViT-B-32-text', threads=2)
        self.by_page = {r['page']: r for r in self.bm25.chunks}
        self.region_vectors, self.regions = [], []
        for path in sorted(index.glob('p*.npz')):
            with np.load(path, allow_pickle=False) as data:
                for vector, name, box in zip(data['vectors'], data['names'], data['boxes']):
                    page = int(path.stem[1:])
                    if page not in self.by_page:
                        continue
                    self.region_vectors.append(vector)
                    self.regions.append((page, str(name), box.tolist()))
        if not self.region_vectors:
            raise ValueError('Visual index has no regions corresponding to text pages')
        self.region_vectors = np.asarray(self.region_vectors, dtype=np.float32)
        self.region_vectors /= np.maximum(np.linalg.norm(self.region_vectors, axis=1, keepdims=True), 1e-12)

    def search(self, query, *, filters, top_k, method, candidates):
        lexical = super().search(query, filters=filters, top_k=top_k, method=method, candidates=candidates)
        query_vector = np.asarray(next(self.embedder.embed([query])), dtype=np.float32)
        query_vector /= np.linalg.norm(query_vector)
        scores = self.region_vectors @ query_vector
        visual_results, seen_pages = [], set()
        for i in np.argsort(scores)[::-1]:
            page, region, box = self.regions[i]
            if page in seen_pages:
                continue
            seen_pages.add(page)
            visual_results.append({'page': page, 'region': region, 'box_pixels': box, 'score': float(scores[i])})
            if len(visual_results) == top_k:
                break
        # Keep lexical evidence and reserve one slot for the strongest distinct visual page.
        rows = [{**r, 'metadata': dict(r['metadata'])} for r in lexical[:max(1, top_k-1)]]
        for match in visual_results:
            if match['page'] not in {r['page'] for r in rows}:
                row = self.by_page[match['page']]
                rows.append({**row, 'metadata': {**row['metadata'], 'visual_match': match},
                             'score': match['score'], 'method': 'clip'})
                break
        for row in rows[:self.vision_limit]:
            visual = describe(self.pdf, row['page'], self.vision_model, 'http://localhost:11434', 960, 256)
            row['text'] += '\n\n[Mô tả ảnh do model tạo, chưa kiểm chứng]\n' + visual['description']
            row['metadata']['vision'] = {k: v for k, v in visual.items() if k != 'description'}
        # Include the visual ranking in trace even when a page was already retrieved lexically.
        for row in rows:
            row['metadata']['clip_candidates'] = visual_results
        return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument('question')
    p.add_argument('--pdf', type=Path, required=True)
    p.add_argument('--image-index', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--visual-index', type=Path)
    p.add_argument('--vision-model', default='qwen2.5vl:3b')
    p.add_argument('--vision-limit', type=int, default=1)
    args = p.parse_args()
    retriever = VisualRetriever(args.pdf, args.image_index, args.visual_index, args.vision_model, args.vision_limit)
    config = {'language': 'vi', 'document_title': 'Việt Nam 2035, bản PDF tiếng Việt',
              'method': 'bm25_caption', 'top_k': 3, 'budget': 18000, 'max_searches': 1}
    trace = run_agent(args.question, Ollama(context_size=16384), retriever, config)
    trace['config'] = {**config, 'vision_model': args.vision_model, 'vision_limit': args.vision_limit,
                       'image_index': str(args.image_index)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(trace, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: trace.get(k) for k in ('status', 'answer', 'citations', 'elapsed_seconds', 'error')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
