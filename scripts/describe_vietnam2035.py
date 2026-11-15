#!/usr/bin/env python3
"""Create unverified page-level visual descriptions from the original PDF.

Requires Poppler and an Ollama vision model. Output never contains page images.
Descriptions are model output, not ground truth; compare them with the original.
"""
import argparse
import base64
import hashlib
import json
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path


def describe(pdf, page, model, url, scale, max_tokens):
    with tempfile.TemporaryDirectory() as temp:
        prefix = Path(temp) / 'page'
        subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page), '-singlefile',
                        '-scale-to', str(scale), '-png', str(pdf), str(prefix)],
                       check=True, capture_output=True)
        image = prefix.with_suffix('.png').read_bytes()
    prompt = ('Mô tả bằng tiếng Việt nội dung thông tin nhìn thấy trong hình, biểu đồ, '
              'sơ đồ hoặc bảng trên trang này. Với từng hình nêu nhãn, trục, đơn vị, '
              'chú giải và xu hướng nếu đọc được. Với bảng nêu tiêu đề, cột và số liệu '
              'đọc chắc chắn. Không suy đoán số liệu. Nếu không đọc được, nói rõ. '
              'Nếu chỉ có chữ thông thường hoặc trang trắng, hãy nói rõ điều đó.')
    payload = {'model': model, 'stream': False,
               'messages': [{'role': 'user', 'content': prompt,
                             'images': [base64.b64encode(image).decode('ascii')]}],
               'options': {'temperature': 0, 'num_predict': max_tokens}}
    req = urllib.request.Request(url.rstrip('/') + '/api/chat',
                                 data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json'})
    started = time.monotonic()
    with urllib.request.urlopen(req, timeout=600) as response:
        result = json.load(response)
    if not result.get('done') or not result.get('message', {}).get('content'):
        raise RuntimeError('Incomplete vision model response')
    return {'id': f'v2035-visual-p{page:04d}', 'pdf_page': page,
            'description': result['message']['content'], 'verification': 'unverified_model_output',
            'model': model, 'render': f'pdftoppm -scale-to {scale} -png',
            'done_reason': result.get('done_reason'), 'max_tokens': max_tokens,
            'input_image_sha256': hashlib.sha256(image).hexdigest(),
            'elapsed_seconds': time.monotonic() - started,
            'prompt_tokens': result.get('prompt_eval_count'), 'completion_tokens': result.get('eval_count')}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('pdf', type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--pages', type=int, nargs='+')
    group.add_argument('--all-pages', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model', default='qwen2.5vl:3b')
    parser.add_argument('--url', default='http://localhost:11434')
    parser.add_argument('--scale', type=int, default=1600)
    parser.add_argument('--max-tokens', type=int, default=1024)
    parser.add_argument('--resume', action='store_true', help='Skip previously successful pages')
    args = parser.parse_args()
    if args.all_pages:
        import re
        info = subprocess.run(['pdfinfo', str(args.pdf)], check=True, capture_output=True, text=True).stdout
        pages = range(1, int(re.search(r'^Pages:\s+(\d+)', info, re.M).group(1)) + 1)
    else:
        pages = args.pages
    completed = set()
    if args.resume and args.output.exists():
        for line in args.output.read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            if row.get('description') and row.get('done_reason') != 'length' and row.get('model') == args.model and row.get('max_tokens') == args.max_tokens and row.get('render') == f'pdftoppm -scale-to {args.scale} -png':
                completed.add(row['pdf_page'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('a', encoding='utf-8') as out:
        for page in pages:
            if page in completed:
                continue
            try:
                row = describe(args.pdf, page, args.model, args.url, args.scale, args.max_tokens)
            except Exception as exc:
                row = {'pdf_page': page, 'error': f'{type(exc).__name__}: {exc}', 'model': args.model}
            out.write(json.dumps(row, ensure_ascii=False) + '\n')
            out.flush()
            print(json.dumps(row, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
