#!/usr/bin/env python3
"""Create or aggregate explicit manual reviews; never infer correctness from gold."""
import argparse
import json
from collections import defaultdict
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--questions', type=Path, required=True)
    p.add_argument('--traces', type=Path, required=True)
    p.add_argument('--reviews', type=Path, required=True)
    p.add_argument('--init', action='store_true')
    a = p.parse_args()
    questions = json.loads(a.questions.read_text(encoding='utf-8'))
    if a.init:
        if a.reviews.exists():
            raise SystemExit('Reviews already exist; refusing to overwrite')
        template = [{'id': q['id'], 'pass': None, 'reason': '', 'original_checked': False,
                     'evidence_checked': ''} for q in questions]
        a.reviews.parent.mkdir(parents=True, exist_ok=True)
        a.reviews.write_text(json.dumps(template, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        return
    reviews = {x['id']: x for x in json.loads(a.reviews.read_text(encoding='utf-8'))}
    if set(reviews) != {q['id'] for q in questions}:
        raise SystemExit('Review IDs do not match the complete question set')
    metrics = defaultdict(lambda: {'pass': 0, 'total': 0, 'errors': 0})
    for q in questions:
        review = reviews[q['id']]
        trace_path = a.traces / f"{q['id']}.json"
        trace = json.loads(trace_path.read_text(encoding='utf-8')) if trace_path.exists() else {'status': 'error'}
        if not isinstance(review['pass'], bool) or not review.get('original_checked') or not review.get('reason') or not review.get('evidence_checked'):
            raise SystemExit(f"Incomplete manual review: {q['id']}")
        if trace['status'] == 'error' and review['pass']:
            raise SystemExit(f"Cannot pass an error: {q['id']}")
        if q['category'] == 'unanswerable' and review['pass'] and trace['status'] != 'abstain':
            raise SystemExit(f"Cannot pass an answer to an unanswerable item: {q['id']}")
        if q['category'] != 'unanswerable' and review['pass'] and (trace['status'] != 'answered' or not trace.get('citations')):
            raise SystemExit(f"Answer lacks required citation: {q['id']}")
        for key in ('all', q['category']):
            metrics[key]['total'] += 1
            metrics[key]['pass'] += int(review['pass'])
            metrics[key]['errors'] += int(trace['status'] == 'error')
    print(json.dumps(dict(metrics), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
