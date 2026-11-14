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


def show(split, config, query_id):
    folder = ROOT / 'results' / split / config
    trace = next(t for t in load(folder / 'traces.json') if t['query_id'] == query_id)
    review = next(r for r in load(folder / 'reviews.json') if r['query_id'] == query_id)
    print(f'\n{split.upper()} / {config} / {query_id}')
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


def main():
    parser = argparse.ArgumentParser(description='Demo bằng trace benchmark thật đã lưu, không gọi model mới')
    parser.add_argument('--scenario', choices=['all', *SCENARIOS], default='all')
    args = parser.parse_args()
    print('PHÁT LẠI TRACE ĐÃ LƯU — không phải suy luận trực tiếp, không tạo số liệu mới.')
    for scenario in SCENARIOS if args.scenario == 'all' else [args.scenario]:
        for row in SCENARIOS[scenario]:
            show(*row)


if __name__ == '__main__':
    main()
