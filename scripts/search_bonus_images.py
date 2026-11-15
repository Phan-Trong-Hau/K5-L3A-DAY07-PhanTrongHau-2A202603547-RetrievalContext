#!/usr/bin/env python3
"""Search a CLIP page/region index; scores are not verified factual evidence."""
import argparse
import json
from pathlib import Path

import numpy as np
from fastembed import TextEmbedding


def main():
    p = argparse.ArgumentParser()
    p.add_argument('query')
    p.add_argument('--index', type=Path, required=True)
    p.add_argument('--top-k', type=int, default=10)
    args = p.parse_args()
    text_model = TextEmbedding(model_name='Qdrant/clip-ViT-B-32-text', threads=2)
    query = np.asarray(next(text_model.embed([args.query])), dtype=np.float32)
    query /= np.linalg.norm(query)
    results = []
    for path in sorted(args.index.glob('p*.npz')):
        with np.load(path, allow_pickle=False) as item:
            vectors = item['vectors']
            vectors = vectors / np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)
            scores = vectors @ query
            for name, box, score in zip(item['names'], item['boxes'], scores):
                results.append({'pdf_page': int(path.stem[1:]), 'region': str(name),
                                'box_pixels': box.tolist(), 'score': float(score),
                                'status': 'unverified_visual_similarity'})
    print(json.dumps(sorted(results, key=lambda x: -x['score'])[:args.top_k], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
