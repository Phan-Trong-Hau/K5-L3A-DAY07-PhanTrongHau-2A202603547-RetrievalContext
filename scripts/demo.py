"""Present recorded benchmark traces. This viewer never runs or changes the agent."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.common import load

SCENARIOS = {
    'improvement': [('dev', 'baseline', 'q04'), ('dev', 'lexical', 'q04')],
    'abstention': [('dev', 'lexical', 'd-missing-1')],
    'failure': [('dev', 'lexical', 'q06')],
    'holdout-error': [('test', 'lexical', 't-missing-1')],
}


def show(split, config, query_id, version='v1'):
    result_root = ROOT / 'results'
    folder = result_root / split / config if split != 'regression' else result_root / 'regression'
    trace = next(t for t in load(folder / 'traces.json') if t['query_id'] == query_id)
    review = next(r for r in load(folder / 'reviews.json') if r['query_id'] == query_id)
    print(f'\n{version.upper()} / {split.upper()} / {config} / {query_id}')
    print('Câu hỏi:', trace['question'])
    searches = [e for e in trace['events'] if e['event'] == 'search']
    print('Số lượt retrieval:', len(searches))
    for event in searches:
        print('Query tool:', event['query'])
        print('Trang trong kết quả:', ', '.join(str(r['page']) for r in event['results']))
    evidence_label = ('Không áp dụng cho câu thiếu evidence' if trace['context_hit'] is None
                      else 'Có' if trace['context_hit'] else 'Không')
    print('Context đủ gold evidence:', evidence_label)
    print('Trạng thái:', trace['status'])
    print('Câu trả lời:', trace['answer'] or trace.get('error', ''))
    if trace['status'] == 'error':
        messages = [e.get('message', {}) for e in trace['events'] if e['event'] == 'model']
        for message in messages:
            if isinstance(message, dict) and message.get('content'):
                print('Raw model output:', message['content'])
    cited = set(trace['citations'])
    for chunk in load(ROOT / 'data/day6/chunks.json'):
        if chunk['id'] in cited:
            print(f"Citation {chunk['id'][:12]}…: {chunk['source']}, trang logic {chunk['page']}")
    if 'answer_grade' in review:
        print(f"Nhãn context {review['context_grade']}/2; answer {review['answer_grade']}/2")
    if 'abstention_correct' in review:
        print('Abstention đúng:', review['abstention_correct'])
    print('Nhận xét đối chiếu:', review['reason'])
    print(f"Thời gian lần chạy đã lưu: {trace['elapsed_seconds']:.2f} giây")
    print('Trace:', folder.relative_to(ROOT) / 'traces.json')


def show_nd13(method, query_id):
    folder = ROOT / 'results/nd13/v2/test' / method
    trace = next(t for t in load(folder / 'traces.json') if t['query_id'] == query_id)
    case = next(q for q in load(ROOT / 'benchmark/nd13/test.json') if q['id'] == query_id)
    review = next(r for r in load(folder / 'reviews.json') if r['query_id'] == query_id)
    print(f'\nNGHỊ ĐỊNH 13 / {method} / {query_id}')
    print('Câu hỏi:', trace['question'])
    print('Đáp án chuẩn:', case.get('expected_answer') or case.get('absence_reason'))
    print('Trạng thái:', trace['status'])
    print('Gold trong top-3:', trace.get('hit3'))
    print('Gold trong context:', trace.get('context_hit'))
    print('Câu trả lời:', trace['answer'] or trace.get('error', ''))
    if review.get('answer_grade') is not None:
        print(f"Điểm answer/context: {review['answer_grade']}/2, {review['context_grade']}/2")
    elif 'abstention_correct' in review:
        print('Từ chối đúng:', review['abstention_correct'])
    print('Nhận xét đối chiếu:', review['reason'])
    chunks = {c['id']: c for c in load(ROOT / 'data/nd13/chunks.json')}
    for cid in trace.get('citations', []):
        chunk = chunks.get(cid)
        if chunk:
            print(f"Citation {cid[:12]}…: trang {chunk['page']}, chương {chunk['metadata'].get('chapter')}")
    print('Trace:', (folder / 'traces.json').relative_to(ROOT))


def main():
    parser = argparse.ArgumentParser(description='Demo bằng trace benchmark thật đã lưu, không gọi model mới')
    parser.add_argument('--scenario', choices=['all', 'new-methods', *SCENARIOS], default='all')
    parser.add_argument('--version', choices=['nd13', 'v1'], default='nd13')
    args = parser.parse_args()
    print('PHÁT LẠI TRACE ĐÃ LƯU — không phải suy luận trực tiếp, không tạo số liệu mới.')
    if args.version == 'nd13':
        scenarios = {
            'all': [('baseline', 'nd13-24'), ('lexical', 'nd13-24'), ('lexical', 'nd13-25'), ('lexical', 'nd13-test-missing-04')],
            'new-methods': [('baseline', 'nd13-23'), ('lexical', 'nd13-23')],
            'failure': [('lexical', 'nd13-25')],
            'abstention': [('lexical', 'nd13-test-missing-04')],
            'improvement': [('baseline', 'nd13-21'), ('lexical', 'nd13-21')],
            'holdout-error': [('baseline', 'nd13-25'), ('lexical', 'nd13-25')],
        }
        for row in scenarios[args.scenario]:
            show_nd13(*row)
    elif args.version == 'v1':
        if args.scenario == 'new-methods':
            parser.error('new-methods is available for --version nd13')
        for scenario in SCENARIOS if args.scenario == 'all' else [args.scenario]:
            for row in SCENARIOS[scenario]:
                show(*row)


if __name__ == '__main__':
    main()
