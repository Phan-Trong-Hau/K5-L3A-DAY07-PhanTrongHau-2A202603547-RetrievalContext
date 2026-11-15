#!/usr/bin/env python3
"""Locate labelled figures and tables in the extracted PDF text.

This detects captions, not visual semantics. Check the original page before use.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

DATA = Path('data/bonus/vietnam2035')
CAPTION = re.compile(r'^\s*(HÌNH|BẢNG)\s+(\d+\.\d+[a-zA-Z]?)\s*[.:]\s*(.*)$')


def inventory(pages):
    for page in pages:
        number = page['metadata']['pdf_page']
        # Front matter contains lists of figures/tables, not the figures themselves.
        if number <= 44:
            continue
        lines = page['text'].splitlines()
        for i, line in enumerate(lines):
            match = CAPTION.match(line)
            if not match:
                continue
            kind, label, title = match.groups()
            following = []
            for continuation in lines[i + 1:i + 4]:
                continuation = continuation.strip()
                if not continuation or CAPTION.match(continuation):
                    break
                following.append(continuation)
            yield {'id': f"v2035-p{number:04d}-{kind.lower()}-{label}",
                   'pdf_page': number, 'kind': kind, 'label': label,
                   'caption_first_line': title.strip(),
                   'following_lines_unverified': following,
                   'locator': f'{kind} {label}, PDF trang {number}',
                   'status': 'caption_detected_visual_not_verified'}


def main():
    pages = [json.loads(line) for line in (DATA / 'pages.jsonl').read_text(encoding='utf-8').splitlines()]
    rows = list(inventory(pages))
    target = DATA / 'visual_inventory.jsonl'
    target.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
    print(f'Detected {len(rows)} captions; visual contents have NOT been verified. Output: {target}')
    if len(sys.argv) > 2:
        raise SystemExit('Usage: python3 scripts/inventory_vietnam2035.py [source.pdf]')
    if len(sys.argv) == 2:
        raw = subprocess.run(['pdfimages', '-list', sys.argv[1]], check=True,
                             capture_output=True, text=True).stdout.splitlines()[2:]
        bitmaps = []
        for line in raw:
            parts = line.split()
            if len(parts) < 15 or not parts[0].isdigit():
                continue
            bitmaps.append({'pdf_page': int(parts[0]), 'object_number': int(parts[1]),
                            'type': parts[2], 'width_px': int(parts[3]), 'height_px': int(parts[4]),
                            'pdf_object_id': parts[10] + ' ' + parts[11],
                            'status': 'bitmap_detected_content_not_verified'})
        target = DATA / 'bitmap_inventory.jsonl'
        target.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in bitmaps), encoding='utf-8')
        print(f'Detected {len(bitmaps)} bitmap/mask objects on {len({x["pdf_page"] for x in bitmaps})} pages. Output: {target}')


if __name__ == '__main__':
    main()
