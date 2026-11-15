#!/usr/bin/env python3
"""Check visual index coverage and file integrity, not semantic accuracy."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--index', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    manifest = json.loads((args.index / 'manifest.json').read_text(encoding='utf-8'))
    valid, missing, errors = [], [], []
    digest = hashlib.sha256()
    for page in range(1, manifest['pdf_pages']+1):
        file = args.index / f'p{page:04d}.npz'
        if not file.exists():
            missing.append(page)
            continue
        try:
            with np.load(file, allow_pickle=False) as data:
                vectors, boxes, names = data['vectors'], data['boxes'], data['names']
                if vectors.shape != (5, 512) or boxes.shape != (5, 4) or names.shape != (5,) or not np.isfinite(vectors).all():
                    raise ValueError('unexpected shape or non-finite values')
                if np.any(boxes[:, 0] >= boxes[:, 2]) or np.any(boxes[:, 1] >= boxes[:, 3]):
                    raise ValueError('invalid region boxes')
            digest.update(file.name.encode('ascii') + b'\0' + hashlib.sha256(file.read_bytes()).digest())
            valid.append(page)
        except Exception as exc:
            errors.append({'page': page, 'error': str(exc)})
    result = {'pdf_pages': manifest['pdf_pages'], 'valid_pages': len(valid), 'missing_pages': missing,
              'invalid_pages': errors, 'regions': len(valid)*5, 'files_digest_sha256': digest.hexdigest(),
              'source_sha256': manifest['source_sha256'], 'model': manifest['model'],
              'note': 'Checks coverage/shape only, not whether visual information is retrievable or accurate.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    if missing or errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
