"""Gold-aware evaluation only; never imported by the model/retrieval modules."""
import statistics


def hit(chunk, gold):
    return any(chunk['source_id'] == g['source_id'] and chunk['page'] == g['page']
               and g['evidence'] in chunk['text'] for g in gold)


def validate_cases(chunks, cases, split):
    if not cases or len({q['id'] for q in cases}) != len(cases):
        raise ValueError('Empty cases or duplicate IDs')
    for q in cases:
        if q.get('split') != split or type(q.get('answerable')) is not bool or not q.get('question', '').strip():
            raise ValueError(f"Invalid case {q.get('id')}")
        if q['answerable']:
            if not q.get('expected_answer') or not q.get('gold'):
                raise ValueError('Missing expected answer/gold')
            if any(not any(hit(c, [g]) for c in chunks) for g in q['gold']):
                raise ValueError(f"Unresolved evidence {q['id']}")
        elif not q.get('absence_reason'):
            raise ValueError('Missing absence audit')


def ratio(n, N):
    return {'n': n, 'N': N, 'rate': n / N if N else None}


def summarize(traces):
    answered = [t for t in traces if t['answerable']]
    successful = [t for t in traces if t['status'] != 'error']
    return {
        'cases': len(traces), 'errors': sum(t['status'] == 'error' for t in traces),
        'hit1': ratio(sum(t['hit1'] for t in answered), len(answered)),
        'hit3': ratio(sum(t['hit3'] for t in answered), len(answered)),
        'context_evidence': ratio(sum(t['context_hit'] for t in answered), len(answered)),
        'tool_use': ratio(sum(any(e['event'] == 'search' for e in t['events']) for t in successful), len(successful)),
        'search_count_distribution': {str(n): sum(sum(e['event'] == 'search' for e in t['events']) == n for t in traces)
                                      for n in sorted({sum(e['event'] == 'search' for e in t['events']) for t in traces})},
        'median_seconds': statistics.median(t['elapsed_seconds'] for t in traces),
        'total_seconds': sum(t['elapsed_seconds'] for t in traces),
        'prompt_tokens': sum(t['usage']['prompt_tokens'] for t in traces),
        'completion_tokens': sum(t['usage']['completion_tokens'] for t in traces),
        'service_cost_usd': sum(t['service_cost_usd'] for t in traces),
        'note': 'Hit@1/3 use ORIGINAL query ranking; context evidence uses final model context. Error quality excluded from manual metrics but counted separately.',
    }
