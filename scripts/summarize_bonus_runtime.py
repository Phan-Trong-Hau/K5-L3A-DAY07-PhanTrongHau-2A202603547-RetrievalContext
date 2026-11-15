#!/usr/bin/env python3
"""Summarize all recorded traces, including errors and model token usage."""
import argparse
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--questions', type=Path, required=True)
    p.add_argument('--traces', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    rows = json.loads(args.questions.read_text(encoding='utf-8'))
    result = {'total_questions': len(rows), 'completed': 0, 'missing_ids': [],
              'errors': 0, 'elapsed_seconds_sum': 0.0, 'prompt_tokens': 0,
              'completion_tokens': 0, 'model_calls': 0, 'service_cost_usd': 0.0,
              'cost_note': 'Ollama local: no service charge; excludes electricity and hardware.'}
    for row in rows:
        path = args.traces / (row['id'] + '.json')
        if not path.exists():
            result['missing_ids'].append(row['id'])
            continue
        trace = json.loads(path.read_text(encoding='utf-8'))
        result['completed'] += 1
        result['errors'] += int(trace['status'] == 'error')
        result['elapsed_seconds_sum'] += trace.get('elapsed_seconds', 0)
        for field in ('prompt_tokens', 'completion_tokens', 'model_calls'):
            result[field] += trace.get('usage', {}).get(field, 0)
        result['service_cost_usd'] += trace.get('service_cost_usd', 0)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
