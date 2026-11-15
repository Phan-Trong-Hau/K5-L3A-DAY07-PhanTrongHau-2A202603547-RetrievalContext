#!/usr/bin/env python3
"""BM25 page-level search over the Vietnam 2035 bonus text index."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.retrieval import BM25


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('query')
    parser.add_argument('--top-k', type=int, default=5)
    args = parser.parse_args()
    with open('data/bonus/vietnam2035/pages.jsonl', encoding='utf-8') as f:
        pages = [json.loads(line) for line in f]
    for row in BM25(pages).search(args.query, top_k=args.top_k):
        print(json.dumps({'score': row['score'], 'pdf_page': row['metadata']['pdf_page'],
                          'id': row['id'], 'text': row['text'][:2000]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
