import hashlib, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))

def digest(path): return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()

class ND13ArtifactTests(unittest.TestCase):
    def test_ocr_snapshot_and_signed_pdf_match_day6_manifest(self):
        manifest=load('data/nd13/source_manifest.json')
        self.assertEqual(digest('data/nd13/13nd.signed.pdf'),manifest['sha256'])
        self.assertEqual(digest('data/nd13/pages.json'),manifest['ocr_text_sha256'])
        pages=load('data/nd13/pages.json')
        self.assertEqual(len(pages),39)
        self.assertTrue(all(p['metadata']['language']=='vi' for p in pages))

    def test_all_frozen_questions_resolve_to_nd13_page_evidence(self):
        questions=load('benchmark/nd13_questions_source.json')
        self.assertEqual(len(questions),20)
        pages=load('data/nd13/pages.json')
        for q in questions:
            self.assertEqual(q['gold_source_id'],'nd13',q['id'])
            self.assertIn(q['evidence_quote'],pages[q['gold_page']-1]['text'],q['id'])
        cases=load('benchmark/nd13/test.json')
        self.assertEqual([q['id'] for q in cases],[q['id'] for q in questions])
        self.assertTrue(all(q['split']=='test' and q['answerable'] for q in cases))

    def test_chunks_and_vectors_share_ids_and_gold_passages(self):
        chunks=load('data/nd13/chunks.json'); vectors=load('data/nd13/vectors.json')
        self.assertEqual(len(chunks),88)
        self.assertEqual([c['id'] for c in chunks],[v['id'] for v in vectors])
        self.assertTrue(all(len(v['vector'])==384 for v in vectors))
        for q in load('benchmark/nd13_questions_source.json'):
            self.assertTrue(any(c['source_id']=='nd13' and c['page']==q['gold_page'] and q['evidence_quote'] in c['text'] for c in chunks),q['id'])

    def test_each_method_has_twenty_real_traces_and_search_event(self):
        cases=load('benchmark/nd13/test.json')
        for method in ('baseline','lexical','hybrid','mmr','rerank'):
            traces=load(f'results/nd13/test/{method}/traces.json')
            self.assertEqual([t['query_id'] for t in traces],[q['id'] for q in cases],method)
            self.assertTrue(all(any(e.get('event')=='search' for e in t['events']) for t in traces),method)
            self.assertTrue(all(t['split']=='test' and t['answerable'] for t in traces),method)

if __name__=='__main__': unittest.main()
