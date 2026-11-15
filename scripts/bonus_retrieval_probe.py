#!/usr/bin/env python3
"""Compare dev retrieval recall; this is not an answer-level benchmark."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.bonus_pilot import PageRetriever


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--questions', type=Path, default=Path('benchmarks/bonus/dev_draft.json'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--top-k', type=int, default=3)
    args = parser.parse_args()
    rows = json.loads(args.questions.read_text(encoding='utf-8'))
    retriever = PageRetriever(Path('data/bonus/vietnam2035/visual_verified.jsonl'))
    results = {}
    for method in ('bm25', 'bm25_caption'):
        questions = []
        for q in rows:
            if not q['pdf_pages']:
                continue
            # Search receives the question only; gold pages are used afterwards.
            ranking = retriever.search(q['question'], filters=None, top_k=args.top_k,
                                       method=method, candidates=20)
            found = [r['metadata']['pdf_page'] for r in ranking]
            questions.append({'id': q['id'], 'retrieved_pages': found,
                              'expected_pages': q['pdf_pages'],
                              'all_evidence_pages_retrieved': set(q['pdf_pages']) <= set(found)})
        results[method] = {'questions': questions,
                           'all_page_recall': sum(q['all_evidence_pages_retrieved'] for q in questions),
                           'total_answerable': len(questions)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: {'all_page_recall': v['all_page_recall'], 'total_answerable': v['total_answerable']}
                      for k, v in results.items()}, ensure_ascii=False))


if __name__ == '__main__':
    main()
