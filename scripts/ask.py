"""Ask a real local agent and save its full trace; no benchmark/gold is loaded."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.agent import Ollama, run_agent
from src.common import load, save
from src.retrieval import Retriever


def main():
    p = argparse.ArgumentParser()
    p.add_argument('question')
    p.add_argument('--config', choices=['baseline', 'lexical', 'hybrid', 'mmr', 'rerank'],
                   help='Default: frozen dev winner, or hybrid before selection')
    p.add_argument('--chapter', help='Only use when the user explicitly requests this chapter')
    p.add_argument('--model', default='qwen3:4b-instruct')
    p.add_argument('--url', default='http://localhost:11434')
    p.add_argument('--output', default='results/demo/trace.json')
    p.add_argument('--dataset', choices=['nd13', 'alice'], default='nd13',
                   help='Nghị định 13 tiếng Việt (default) or historical Alice corpus')
    args = p.parse_args()
    config_name = args.config or 'rerank'
    data_dir = 'data/nd13' if args.dataset == 'nd13' else 'data/day6'
    store = '.qdrant_nd13' if args.dataset == 'nd13' else '.qdrant'
    config = load('configs/experiments.json')[config_name]
    if args.dataset == 'nd13':
        config = {**config, 'language': 'vi',
                  'document_title': 'Nghị định số 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân'}
    retriever = Retriever(data=data_dir, store=store)
    try:
        result = run_agent(args.question, Ollama(args.model, args.url, context_size=4096), retriever,
                           config,
                           filters={'chapter': args.chapter} if args.chapter else None)
    finally:
        retriever.close()
    save(args.output, result)
    print(result['status'], result['answer'], sep='\n')
    if result['status'] == 'error':
        print(result['error'], file=sys.stderr)
        raise SystemExit(1)
    print(f"Dataset: {args.dataset}; config: {config_name}; trace: {args.output}; {result['elapsed_seconds']:.2f}s")


if __name__ == '__main__':
    main()
