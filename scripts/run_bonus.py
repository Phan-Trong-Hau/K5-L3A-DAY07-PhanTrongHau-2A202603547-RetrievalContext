#!/usr/bin/env python3
"""Run a bonus split without supplying answers or gold locations to the agent."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.agent import Ollama
from src.agent_v2 import run_agent
from scripts.bonus_pilot import PageRetriever


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--questions', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--top-k', type=int, default=3)
    parser.add_argument('--method', choices=('bm25', 'bm25_caption'), default='bm25')
    parser.add_argument('--max-searches', type=int, default=1)
    parser.add_argument('--visual-index', type=Path)
    parser.add_argument('--model', default='qwen3:4b-instruct')
    args = parser.parse_args()
    rows = json.loads(args.questions.read_text(encoding='utf-8'))
    if len({row['id'] for row in rows}) != len(rows):
        raise ValueError('Question IDs must be unique')
    config = {'language': 'vi', 'document_title': 'Việt Nam 2035, bản PDF tiếng Việt',
              'method': args.method, 'top_k': args.top_k, 'budget': 18000,
              'max_searches': args.max_searches}
    retriever = PageRetriever(args.visual_index)
    provider = Ollama(model=args.model, context_size=16384)
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {'config': config, 'model': args.model, 'question_file': str(args.questions),
                'question_file_sha256': hashlib.sha256(args.questions.read_bytes()).hexdigest(),
                'visual_index': str(args.visual_index) if args.visual_index else None,
                'visual_index_sha256': hashlib.sha256(args.visual_index.read_bytes()).hexdigest() if args.visual_index else None,
                'corpus_sha256': hashlib.sha256(Path('data/bonus/vietnam2035/pages.jsonl').read_bytes()).hexdigest(),
                'code_sha256': {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in (
                    'scripts/run_bonus.py', 'scripts/bonus_pilot.py', 'src/agent.py',
                    'src/agent_v2.py', 'src/retrieval.py')},
                'note': 'Exploratory run: no answer keys or gold page locations enter run_agent.'}
    manifest_file = args.output / 'manifest.json'
    if manifest_file.exists() and json.loads(manifest_file.read_text(encoding='utf-8')) != manifest:
        raise ValueError('Output exists with a different configuration; choose a new directory')
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    for row in rows:
        target = args.output / f"{row['id']}.json"
        if target.exists():
            continue
        trace = run_agent(row['question'], provider, retriever, config)
        trace['id'] = row['id']
        target.write_text(json.dumps(trace, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(json.dumps({'id': row['id'], 'status': trace['status'],
                          'seconds': trace['elapsed_seconds'], 'error': trace.get('error')}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
