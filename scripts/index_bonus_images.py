#!/usr/bin/env python3
"""Build a page-and-quadrant CLIP image index from the original PDF.

Needs Poppler, Pillow, NumPy and fastembed. Images are not persisted.
Vectors are retrieval aids, not verified descriptions or answers.
"""
import argparse
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from fastembed import ImageEmbedding
from PIL import Image

MODEL = 'Qdrant/clip-ViT-B-32-vision'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def page_images(pdf, page, size):
    with tempfile.TemporaryDirectory() as temp:
        prefix = Path(temp) / 'page'
        subprocess.run(['pdftoppm', '-f', str(page), '-l', str(page), '-singlefile',
                        '-scale-to', str(size), '-png', str(pdf), str(prefix)],
                       check=True, capture_output=True)
        image = Image.open(prefix.with_suffix('.png')).convert('RGB')
        w, h = image.size
        regions = [('full', (0, 0, w, h)), ('top_left', (0, 0, w//2, h//2)),
                   ('top_right', (w//2, 0, w, h//2)),
                   ('bottom_left', (0, h//2, w//2, h)),
                   ('bottom_right', (w//2, h//2, w, h))]
        return [(name, box, image.crop(box)) for name, box in regions]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('pdf', type=Path)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--pages', type=int, nargs='+', help='Omit to process every PDF page')
    p.add_argument('--size', type=int, default=1200)
    p.add_argument('--threads', type=int, default=4)
    args = p.parse_args()
    info = subprocess.run(['pdfinfo', str(args.pdf)], check=True, capture_output=True, text=True).stdout
    total = int(re.search(r'^Pages:\s+(\d+)', info, re.M).group(1))
    pages = args.pages if args.pages else range(1, total+1)
    if any(not 1 <= n <= total for n in pages):
        raise SystemExit('Page out of range')
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {'source_sha256': sha(args.pdf), 'pdf_pages': total, 'model': MODEL,
                'render_scale': args.size, 'regions_per_page': 5,
                'verification': 'unverified_visual_embeddings', 'cost_usd': 0}
    mfile = args.output / 'manifest.json'
    if mfile.exists() and json.loads(mfile.read_text(encoding='utf-8')) != manifest:
        raise SystemExit('Index configuration or PDF changed; use a new output directory')
    mfile.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    model = ImageEmbedding(model_name=MODEL, threads=args.threads)
    for page in pages:
        target = args.output / f'p{page:04d}.npz'
        if target.exists():
            continue
        try:
            regions = page_images(args.pdf, page, args.size)
            vectors = np.asarray(list(model.embed([r[2] for r in regions])), dtype=np.float32)
            if vectors.shape != (5, 512) or not np.isfinite(vectors).all():
                raise ValueError(f'Unexpected vector shape or values: {vectors.shape}')
            temporary = args.output / f'.p{page:04d}.partial.npz'
            np.savez_compressed(temporary, vectors=vectors,
                                boxes=np.asarray([r[1] for r in regions]),
                                names=np.asarray([r[0] for r in regions]))
            temporary.replace(target)
            print(json.dumps({'pdf_page': page, 'status': 'ok'}), flush=True)
        except Exception as exc:
            error = {'pdf_page': page, 'status': 'error', 'error': str(exc)}
            with (args.output / 'errors.jsonl').open('a', encoding='utf-8') as errors:
                errors.write(json.dumps(error, ensure_ascii=False) + '\n')
            print(json.dumps(error, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
