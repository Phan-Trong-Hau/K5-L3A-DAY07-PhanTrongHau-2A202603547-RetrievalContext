"""Run one split, append complete real traces, and freeze dev selection before test."""
import argparse
import importlib.metadata
import json
import platform
import urllib.request
from pathlib import Path

from .agent import Ollama, run_agent
from .common import load, save, sha256, utc
from .evaluation import hit, summarize, validate_cases
from .retrieval import Retriever


def run(args):
    configs = load(args.configs)
    # Read only the requested split, not held-out test evidence during dev runs.
    cases_path = Path('benchmark') / f'{args.split}.json'
    cases = load(cases_path)
    if args.split == 'test':
        selection = load('results/selection.json')
        if selection['config_file_sha256'] != sha256(args.configs):
            raise ValueError('Configurations changed since dev freeze')
        if selection['corpus_sha256'] != sha256('data/day6/chunks.json') or selection['test_sha256'] != sha256(cases_path):
            raise ValueError('Corpus/holdout changed since freeze')
        for name, expected in selection['code_sha256'].items():
            if sha256(name) != expected:
                raise ValueError(f'Agent code changed since freeze: {name}')
        names = list(dict.fromkeys(['baseline', selection['selected']]))
    else:
        if Path('results/selection.json').exists():
            raise ValueError('Dev is already frozen; start a new experiment rather than silently retuning')
        names = args.names or list(configs)
    provider = Ollama(model=args.model, url=args.url)
    with urllib.request.urlopen(args.url.rstrip('/') + '/api/tags', timeout=10) as response:
        tags = json.load(response)
    tag = next((m for m in tags['models'] if m['name'] == args.model), None)
    if tag is None:
        raise ValueError('Requested model is not installed; run ollama pull first')
    if args.split == 'test' and tag['digest'] != selection['model_digest']:
        raise ValueError('Model changed since dev freeze')
    retriever = Retriever()
    try:
        validate_cases(retriever.chunks, cases, args.split)
        for name in names:
            config = configs[name]
            out = Path('results') / args.split / name
            out.mkdir(parents=True, exist_ok=True)
            path = out / 'traces.json'
            traces = load(path) if path.exists() else []
            # Resume only an identical run. Fail rather than mix configurations or model snapshots.
            manifest = {'model': args.model, 'model_digest': tag['digest'], 'config': config,
                        'benchmark_sha256': sha256(cases_path), 'corpus_sha256': sha256('data/day6/chunks.json'),
                        'code_sha256': {str(p): sha256(p) for p in sorted(Path('src').glob('*.py'))}}
            if traces and load(out / 'manifest.json') != manifest:
                raise ValueError(f'Cannot resume changed experiment: {out}')
            save(out / 'manifest.json', manifest)
            done = {t['query_id'] for t in traces}
            if not done <= {q['id'] for q in cases} or len(done) != len(traces):
                raise ValueError('Invalid existing trace IDs')
            for q in cases:
                if q['id'] in done:
                    continue
                trace = run_agent(q['question'], provider, retriever, config, filters=q.get('filter'))
                trace.update(query_id=q['id'], split=args.split, configuration=name, config=config,
                             answerable=q['answerable'])
                # Separate original-query retrieval measurement from any model rewrite/multi-hop ranking.
                try:
                    ranking = retriever.search(q['question'], filters=q.get('filter'), top_k=3,
                                               method=config['method'], candidates=config.get('candidates', 20))
                    trace['original_query_results'] = ranking
                    gold = q.get('gold', [])
                    trace['hit1'] = bool(ranking and hit(ranking[0], gold)) if q['answerable'] else None
                    trace['hit3'] = any(hit(c, gold) for c in ranking) if q['answerable'] else None
                    trace['context_hit'] = any(hit(c, gold) for c in retriever.chunks if c['id'] in trace['context_ids']) if q['answerable'] else None
                except Exception as exc:
                    trace.update(status='error', evaluation_error=f'{type(exc).__name__}: {exc}', hit1=False, hit3=False, context_hit=False)
                traces.append(trace)
                save(path, traces)
                save(out / 'summary.json', summarize(traces))
                print(f"{args.split}/{name}/{q['id']}: {trace['status']} | {trace['elapsed_seconds']:.1f}s | {trace['answer']}", flush=True)
            save(out / 'environment.json', {'recorded_at': utc(), 'python': platform.python_version(),
                'versions': {p: importlib.metadata.version(p) for p in ['fastembed', 'qdrant-client', 'onnxruntime', 'numpy']},
                'ollama_tag': tag, 'cost_note': 'Local inference; USD 0 service fees, excluding electricity/hardware.'})
    finally:
        retriever.close()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--split', choices=['dev', 'test'], required=True)
    p.add_argument('--configs', default='configs/experiments.json')
    p.add_argument('--names', nargs='+')
    p.add_argument('--model', default='qwen3:4b-instruct')
    p.add_argument('--url', default='http://localhost:11434')
    run(p.parse_args())


if __name__ == '__main__':
    main()
