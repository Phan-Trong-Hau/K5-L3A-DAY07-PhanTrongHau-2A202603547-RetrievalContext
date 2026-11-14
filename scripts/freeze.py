"""Select from audited DEV results, write hashes, then permit held-out test."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import load, save, sha256, utc
from src.evaluation import ratio


def audit(cases, traces, reviews):
    by_id = {r['query_id']: r for r in reviews}
    if len(by_id) != len(reviews) or {t['query_id'] for t in traces} != {q['id'] for q in cases}:
        raise ValueError('Incomplete/duplicate trace or review IDs')
    question_by_id = {q['id']: q for q in cases}
    stats = {'answer_grades': {'0': 0, '1': 0, '2': 0}, 'context_grades': {'0': 0, '1': 0, '2': 0},
             'errors': 0, 'citation_support': ratio(0, 0), 'citation_coverage': ratio(0, 0),
             'abstention': ratio(0, 0), 'false_abstention': ratio(0, 0)}
    citation_n = citation_N = coverage_n = coverage_N = abstain_n = abstain_N = false_n = false_N = 0
    selection_total = selection_n = 0
    for t in traces:
        q = question_by_id[t['query_id']]
        if q['answerable']:
            selection_n += 1
        if t['status'] == 'error':
            stats['errors'] += 1
        r = by_id.get(q['id'])
        if r is None or not r.get('reason') or not r.get('reviewer'):
            raise ValueError(f"Missing audit/reason/reviewer: {q['id']}")
        support = r.get('citation_support')
        if not isinstance(support, list) or len(support) != len(t['citations']) or any(type(s) is not bool for s in support):
            raise ValueError('One support boolean per citation is required')
        citation_n += sum(ok and cid in t['context_ids'] for cid, ok in zip(t['citations'], support))
        citation_N += len(support)
        if t['status'] == 'answered':
            coverage_N += 1
            coverage_n += bool(t['citations'])
        if q['answerable']:
            grade, context = r.get('answer_grade'), r.get('context_grade')
            if type(grade) is not int or grade not in (0, 1, 2) or type(context) is not int or context not in (0, 1, 2):
                raise ValueError('Answer and context grades must be 0/1/2')
            if t['status'] in ('abstain', 'error') and grade != 0:
                raise ValueError('Abstained answerable case must be graded zero')
            stats['answer_grades'][str(grade)] += 1
            stats['context_grades'][str(context)] += 1
            selection_total += grade
            false_N += 1
            false_n += t['status'] == 'abstain'
        else:
            if type(r.get('abstention_correct')) is not bool:
                raise ValueError('Explicit abstention correctness review required')
            if r['abstention_correct'] and t['status'] != 'abstain':
                raise ValueError('Correct abstention requires abstain status')
            abstain_N += 1
            abstain_n += r['abstention_correct'] and t['status'] == 'abstain'
    n = sum(stats['answer_grades'].values())
    stats.update(grounded_mean=(stats['answer_grades']['1'] + 2 * stats['answer_grades']['2']) / n if n else None,
                 selection_mean_errors_zero=selection_total / selection_n if selection_n else 0,
                 citation_support=ratio(citation_n, citation_N), citation_coverage=ratio(coverage_n, coverage_N),
                 abstention=ratio(abstain_n, abstain_N), false_abstention=ratio(false_n, false_N))
    return stats


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--split', choices=['dev', 'test'], required=True)
    args = p.parse_args()
    configs = load('configs/experiments.json')
    if args.split == 'dev' and Path('results/selection.json').exists():
        raise ValueError('Selection already frozen; do not overwrite')
    cases = load(f'benchmark/{args.split}.json')
    comparison = {}
    for folder in sorted(Path(f'results/{args.split}').iterdir()):
        if not (folder / 'traces.json').exists():
            continue
        audited = audit(cases, load(folder / 'traces.json'), load(folder / 'reviews.json'))
        save(folder / 'audit_summary.json', audited)
        comparison[folder.name] = {**load(folder / 'summary.json'), **audited}
    save(f'results/{args.split}/comparison.json', comparison)
    if args.split == 'dev':
        if set(comparison) != set(configs):
            raise ValueError('All configured methods must finish dev before selection')
        winner = min(comparison, key=lambda name: (
            -comparison[name]['selection_mean_errors_zero'],
            -(comparison[name]['abstention']['rate'] or 0),
            -(comparison[name]['context_evidence']['rate'] or 0),
            comparison[name]['median_seconds'], name))
        manifests = [load(f'results/dev/{name}/manifest.json') for name in comparison]
        if len({m['model_digest'] for m in manifests}) != 1:
            raise ValueError('Dev configurations used different model versions')
        if any(m['code_sha256'] != manifests[0]['code_sha256'] for m in manifests):
            raise ValueError('Dev configurations used different code; rerun comparable experiments')
        if any(sha256(name) != expected for name, expected in manifests[0]['code_sha256'].items()):
            raise ValueError('Code changed after dev; cannot freeze unmeasured code')
        save('results/selection.json', {'selected': winner, 'frozen_at': utc(),
            'criterion': load('benchmark/protocol.json')['selection'],
            'config': configs[winner], 'config_file_sha256': sha256('configs/experiments.json'),
            'dev_sha256': sha256('benchmark/dev.json'), 'test_sha256': sha256('benchmark/test.json'),
            'corpus_sha256': sha256('data/day6/chunks.json'), 'code_sha256': manifests[0]['code_sha256'],
            'model_digest': manifests[0]['model_digest'],
            'review_sha256': {name: sha256(f'results/dev/{name}/reviews.json') for name in comparison},
            'dev_comparison': comparison})
        print(f'Dev selection frozen: {winner}. Test may now run.')
    else:
        print('Test audits aggregated; no configuration changes made.')


if __name__ == '__main__':
    main()
