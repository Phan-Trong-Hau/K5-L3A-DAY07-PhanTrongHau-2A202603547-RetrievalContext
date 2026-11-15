#!/usr/bin/env python3
"""Exploratory v4: explicit evidence checking for visual locators and multi-part answers.

This policy was created after inspecting the draft test. A NEW held-out test is
required before reporting a test score for it; never reuse that draft as test.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.bonus_pilot import PageRetriever
from src.agent import Ollama
from src.agent_v2 import run_agent


class CarefulOllama(Ollama):
    def chat(self, messages, tools):
        messages = [dict(m) for m in messages]
        messages[0]['content'] += '''\nKhi đọc bảng, đối chiếu đủ hàng, cột, năm và đơn vị. Với biểu đồ, dùng mô tả
hình đã kiểm chứng trong context, đối chiếu đúng nhóm, chú giải, vị trí (trên/dưới,
trái/phải), năm và đơn vị. Không suy đoán thông tin không ghi trong hình.
Câu nhiều phần phải trả lời từng phần và trích dẫn tất cả trang cần thiết; nếu đã
truy xuất thấy bằng chứng thì không được từ chối. Nếu thiếu bằng chứng, chỉ nêu
không đủ bằng chứng, không bổ sung khẳng định khác.'''
        return super().chat(messages, tools)


def run_v3(question, provider, retriever, config):
    trace = run_agent(question, provider, retriever, config)
    if trace['status'] == 'abstain':
        # Preserve the raw model output in events for audit. A bounded, generic
        # refusal cannot accidentally add unsupported claims or fabricate facts.
        trace['events'].append({'event': 'abstention_normalization', 'original': trace['answer']})
        trace['answer'] = 'ABSTAIN: Không đủ bằng chứng trong các đoạn đã truy xuất để trả lời câu hỏi.'
    trace['policy'] = 'v4_visual_locator_and_multihop_evidence'
    return trace


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--questions', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--visual-index', type=Path, required=True)
    p.add_argument('--model', default='qwen3:4b-instruct')
    args = p.parse_args()
    rows = json.loads(args.questions.read_text(encoding='utf-8'))
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Question IDs must be unique')
    config = {'language': 'vi', 'document_title': 'Việt Nam 2035, bản PDF tiếng Việt',
              'method': 'bm25_caption', 'top_k': 3, 'budget': 18000, 'max_searches': 1}
    def sha(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    manifest = {'config': config, 'policy': 'v4_visual_locator_and_multihop_evidence',
                'model': args.model, 'question_file_sha256': sha(args.questions),
                'visual_index_sha256': sha(args.visual_index),
                'corpus_sha256': sha('data/bonus/vietnam2035/pages.jsonl'),
                'code_sha256': {f: sha(f) for f in ('scripts/run_bonus_v4.py', 'scripts/bonus_pilot.py',
                                'src/agent.py', 'src/agent_v2.py', 'src/retrieval.py')},
                'note': 'Developed after draft test; new visual and protocol policy; select using dev, then use a separate frozen test.'}
    args.output.mkdir(parents=True, exist_ok=True)
    mf = args.output / 'manifest.json'
    if mf.exists() and json.loads(mf.read_text(encoding='utf-8')) != manifest:
        raise ValueError('Output exists with a different configuration')
    mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    retriever, provider = PageRetriever(args.visual_index), CarefulOllama(model=args.model, context_size=16384)
    for row in rows:
        target = args.output / (row['id']+'.json')
        if target.exists():
            continue
        trace = run_v3(row['question'], provider, retriever, config)
        trace['id'] = row['id']
        target.write_text(json.dumps(trace, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(json.dumps({'id': row['id'], 'status': trace['status'],
                          'seconds': trace['elapsed_seconds'], 'error': trace.get('error')}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
