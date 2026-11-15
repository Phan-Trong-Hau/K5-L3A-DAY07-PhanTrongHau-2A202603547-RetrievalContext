#!/usr/bin/env python3
"""Check basic bonus benchmark structure, not factual validity or independence."""
import json
from collections import Counter
from pathlib import Path


def main():
    base = Path('benchmarks/bonus')
    dev = json.loads((base / 'dev_draft.json').read_text(encoding='utf-8'))
    test = json.loads((base / 'test_draft.json').read_text(encoding='utf-8'))
    dev_counts, test_counts = Counter(x['category'] for x in dev), Counter(x['category'] for x in test)
    requirements = {'table': 6, 'image': 5, 'chart': 5, 'multi_hop': 4, 'text': 4, 'unanswerable': 6}
    assert len(dev) >= 18 and dev_counts['unanswerable'] >= 3 and len(dev)-dev_counts['unanswerable'] >= 15
    assert len(test) >= 30 and all(test_counts[k] >= v for k, v in requirements.items())
    assert len({x['id'] for x in dev + test}) == len(dev + test)
    assert not ({x['question'].strip().casefold() for x in dev} & {x['question'].strip().casefold() for x in test})
    for row in dev + test:
        assert all(row.get(k) for k in ('id', 'category', 'question', 'expected', 'evidence'))
        assert row['category'] == 'unanswerable' or row['pdf_pages']
    print(json.dumps({'dev': dict(dev_counts), 'test': dict(test_counts),
                      'warning': 'Structural checks only; original-source audits and semantic independence still required.'},
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
