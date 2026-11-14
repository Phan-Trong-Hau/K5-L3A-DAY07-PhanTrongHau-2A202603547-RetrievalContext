"""Export a copy of Day 6's frozen C collection, without touching its store."""
import argparse
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import load, save, sha256, utc


def main():
    from qdrant_client import QdrantClient
    p = argparse.ArgumentParser()
    p.add_argument('--day6', type=Path, required=True)
    args = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    origin = args.day6.resolve()
    out = root / 'data/day6'
    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp:
        shutil.copytree(origin / '.qdrant', Path(temp) / 'qdrant')
        client = QdrantClient(path=str(Path(temp) / 'qdrant'))
        try:
            points, offset = [], None
            while True:
                rows, offset = client.scroll('C', offset=offset, limit=128, with_vectors=True)
                points.extend(rows)
                if offset is None:
                    break
        finally:
            client.close()
    points.sort(key=lambda r: r.payload['chunk_id'])
    chunks = [{'id': r.payload['chunk_id'], 'source_id': r.payload['document_id'],
               'source': r.payload['source'], 'page': r.payload['page'],
               'text': r.payload['text'], 'metadata': r.payload['metadata']} for r in points]
    save(out / 'chunks.json', chunks)
    save(out / 'vectors.json', [{'id': c['id'], 'point_id': str(r.id), 'vector': r.vector}
                               for c, r in zip(chunks, points)])
    for file in ('alice.txt', 'manifest.json', 'pages.json'):
        shutil.copy2(origin / 'data' / file, out / file)
    save(out / 'embedding.json', load(origin / 'results/model_snapshot.json'))
    run = load(origin / 'results/run.json')
    save(out / 'provenance.json', {
        'exported_at': utc(), 'day6_collection': 'C', 'chunk_count': len(chunks),
        'source_repository': 'https://github.com/Phan-Trong-Hau/K5-L3A-DAY06-PhanTrongHau-2A202603547-DataIngestion',
        'embedding_model': run['started_model'], 'dimensions': run['dimensions'],
        'query_embedding': 'FastEmbed TextEmbedding.query_embed; same Day 6 model snapshot',
        'distance': 'Cosine', 'day6_run': run,
        'sha256': {name: sha256(out / name) for name in ('chunks.json', 'vectors.json', 'alice.txt', 'pages.json', 'manifest.json', 'embedding.json')},
        'page_convention': '82 logical paragraph-group units from Day 6, not physical PDF pages',
        'permission': 'Public-domain Lewis Carroll text; original Gutenberg license retained in alice.txt',
    })
    # Only the Day 6 dev is reused. Day 6 test was already evaluated, so Day 7 needs a new holdout.
    dev = []
    for q in load(origin / 'benchmark/questions.json'):
        if q['split'] == 'dev':
            dev.append({'id': q['id'], 'split': 'dev', 'question': q['question'],
                        'answerable': True, 'expected_answer': q['expected_answer'],
                        'filter': q.get('filter', {}),
                        'gold': [{'source_id': q['gold_source_id'], 'page': q['gold_page'], 'evidence': q['evidence_quote']}]})
    save(root / 'benchmark/dev.json', dev)
    print(f'Exported {len(chunks)} chunks and real vectors from collection C; {len(dev)} dev questions.')


if __name__ == '__main__':
    main()
