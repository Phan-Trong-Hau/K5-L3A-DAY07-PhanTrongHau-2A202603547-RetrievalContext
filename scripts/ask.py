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
    p.add_argument('--config', choices=['baseline', 'lexical', 'hybrid'],
                   help='Default: frozen dev winner, or hybrid before selection')
    p.add_argument('--chapter', help='Only use when the user explicitly requests this chapter')
    p.add_argument('--model', default='qwen3:4b-instruct')
    p.add_argument('--url', default='http://localhost:11434')
    p.add_argument('--output', default='results/demo/trace.json')
    args = p.parse_args()
    config_name = args.config or (load('results/selection.json')['selected']
                                 if Path('results/selection.json').exists() else 'hybrid')
    retriever = Retriever()
    try:
        result = run_agent(args.question, Ollama(args.model, args.url), retriever,
                           load('configs/experiments.json')[config_name],
                           filters={'chapter': args.chapter} if args.chapter else None)
    finally:
        retriever.close()
    save(args.output, result)
    print(result['status'], result['answer'], sep='\n')
    if result['status'] == 'error':
        print(result['error'], file=sys.stderr)
        raise SystemExit(1)
    print(f"Config: {config_name}; trace: {args.output}; {result['elapsed_seconds']:.2f}s")


if __name__ == '__main__':
    main()
