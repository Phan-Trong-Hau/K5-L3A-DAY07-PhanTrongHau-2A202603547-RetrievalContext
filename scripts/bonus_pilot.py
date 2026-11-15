#!/usr/bin/env python3
"""Exploratory bonus retrieval run; this is not the ADVANCED test benchmark."""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.agent import Ollama
from src.agent_v2 import run_agent
from src.retrieval import BM25


class PageRetriever:
    def __init__(self, visual_index=None):
        path = Path('data/bonus/vietnam2035/pages.jsonl')
        pages = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        for row in pages:
            row['page'] = row['metadata']['pdf_page']
            row['source'] = 'Việt Nam 2035, PDF tiếng Việt'
        if visual_index:
            by_page = {row['page']: row for row in pages}
            for line in visual_index.read_text(encoding='utf-8').splitlines():
                visual = json.loads(line)
                if visual.get('description') and visual['pdf_page'] in by_page:
                    status = visual.get('verification', 'unverified')
                    by_page[visual['pdf_page']]['text'] += (
                        f'\n\n[Mô tả hình; trạng thái kiểm chứng: {status}]\n' + visual['description'])
        self.bm25 = BM25(pages)

    def search(self, query, *, filters, top_k, method, candidates):
        if filters or method not in ('bm25', 'bm25_caption'):
            raise ValueError('Unsupported pilot retrieval configuration')
        if method == 'bm25':
            return self.bm25.search(query, top_k=top_k)
        ranking = self.bm25.search(query, top_k=len(self.bm25.chunks))
        labels = []
        for match in re.finditer(r'\b(bảng|hình)\s+(\d+\.\d+)\b', query, re.I):
            kind, number = match.groups()
            labels.append((kind, number))
            following = re.match(r'\s*(?:và|,)\s*(?:(bảng|hình)\s+)?(\d+\.\d+)\b',
                                 query[match.end():], re.I)
            if following:
                labels.append((following.group(1) or kind, following.group(2)))
        def has_caption(row):
            return any(re.search(r'^\s*' + re.escape(kind.upper()) + r'\s+' + re.escape(number) + r'\s*[.:]',
                                 row['text'], re.M) for kind, number in labels)
        return sorted(ranking, key=lambda row: (not has_caption(row), -row['score'], row['id']))[:top_k]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('question')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--top-k', type=int, default=3)
    parser.add_argument('--visual-index', type=Path, help='JSONL visual descriptions; unverified')
    args = parser.parse_args()
    config = {'language': 'vi', 'document_title': 'Việt Nam 2035, bản PDF tiếng Việt',
              'method': 'bm25', 'top_k': args.top_k, 'budget': 18000, 'max_searches': 2}
    trace = run_agent(args.question, Ollama(context_size=16384), PageRetriever(args.visual_index), config)
    config['visual_index'] = str(args.visual_index) if args.visual_index else None
    trace['config'] = config
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: trace.get(k) for k in ('status', 'answer', 'citations', 'elapsed_seconds', 'error')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
