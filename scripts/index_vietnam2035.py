#!/usr/bin/env python3
"""Build a page-addressable text index for the official Vietnam 2035 PDF.

Download the source yourself (see data/bonus/vietnam2035/README.md), then run:
  python scripts/index_vietnam2035.py /path/to/vietnam2035_vi.pdf
Requires Poppler's pdftotext and pdfinfo commands.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

OUT = Path('data/bonus/vietnam2035')


def run(*args):
    return subprocess.run(args, check=True, capture_output=True).stdout.decode('utf-8', 'replace')


def main(pdf):
    pdf = Path(pdf)
    info = run('pdfinfo', str(pdf))
    pages = int(re.search(r'^Pages:\s+(\d+)', info, re.M).group(1))
    raw = run('pdftotext', '-layout', '-enc', 'UTF-8', str(pdf), '-')
    physical = raw.split('\f')
    records, skipped = [], []
    for number, text in enumerate(physical[:pages], 1):
        text = '\n'.join(line.rstrip() for line in text.splitlines()).strip()
        if len(re.sub(r'\s', '', text)) < 30:
            skipped.append({'pdf_page': number, 'reason': 'no extractable text or under 30 non-whitespace characters'})
            continue
        # Keep original page boundaries. Do not merge across pages: citations remain auditable.
        records.append({'id': f'v2035-p{number:04d}', 'text': text,
                        'metadata': {'pdf_page': number, 'source': 'Vietnam 2035 (Vietnamese, 2016)',
                                     'content_type': 'page_text'}})
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / 'pages.jsonl').open('w', encoding='utf-8') as f:
        for row in records:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')
    (OUT / 'index_manifest.json').write_text(json.dumps({
        'document': 'Việt Nam 2035: Hướng tới Thịnh vượng, Sáng tạo, Công bằng và Dân chủ',
        'edition_year': 2016, 'pdf_pages': pages, 'indexed_pages': len(records),
        'unprocessed_pages': skipped, 'extraction': 'Poppler pdftotext -layout; page-preserving; no OCR',
        'source_sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
        'index_sha256': hashlib.sha256((OUT / 'pages.jsonl').read_bytes()).hexdigest()
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Indexed {len(records)}/{pages} physical pages; skipped {len(skipped)}. Output: {OUT}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python scripts/index_vietnam2035.py /path/to/source.pdf')
    main(sys.argv[1])
