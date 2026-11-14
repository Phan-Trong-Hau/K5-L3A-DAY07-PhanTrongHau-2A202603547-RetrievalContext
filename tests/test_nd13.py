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

    def test_v2_splits_meet_counts_and_have_disjoint_ids(self):
        dev=load('benchmark/nd13/dev.json'); test=load('benchmark/nd13/test.json')
        self.assertEqual((len(dev),sum(q['answerable'] for q in dev)),(22,20))
        self.assertEqual((len(test),sum(q['answerable'] for q in test)),(7,5))
        self.assertEqual(len({q['id'] for q in dev}),len(dev))
        self.assertEqual(len({q['id'] for q in test}),len(test))
        self.assertFalse({q['id'] for q in dev}&{q['id'] for q in test})
        self.assertEqual(load('benchmark/nd13/protocol.json')['version'],2)

    def test_every_answerable_gold_quote_exists_on_its_source_page_and_chunk(self):
        pages=load('data/nd13/pages.json'); chunks=load('data/nd13/chunks.json')
        for split in ('dev','test'):
            for q in load(f'benchmark/nd13/{split}.json'):
                if not q['answerable']: continue
                for gold in q['gold']:
                    self.assertIn(gold['evidence'],pages[gold['page']-1]['text'],q['id'])
                    self.assertTrue(any(c['source_id']==gold['source_id'] and c['page']==gold['page'] and gold['evidence'] in c['text'] for c in chunks),q['id'])

    def test_chunks_and_vectors_share_ids_and_gold_passages(self):
        chunks=load('data/nd13/chunks.json'); vectors=load('data/nd13/vectors.json')
        self.assertEqual(len(chunks),88)
        self.assertEqual([c['id'] for c in chunks],[v['id'] for v in vectors])
        self.assertTrue(all(len(v['vector'])==384 for v in vectors))

    def test_archived_v1_traces_remain_available_for_all_methods(self):
        old=load('benchmark/nd13/external_v1.json')
        self.assertEqual(len(old),20)
        for method in ('baseline','lexical','hybrid','mmr','rerank'):
            traces=load(f'results/nd13/external_v1/{method}/traces.json')
            self.assertEqual(len(traces),20,method)

    def test_dev_has_all_five_methods_and_full_trace_coverage(self):
        cases=load('benchmark/nd13/dev.json')
        for method in ('baseline','lexical','hybrid','mmr','rerank'):
            traces=load(f'results/nd13/v2/dev/{method}/traces.json')
            self.assertEqual([t['query_id'] for t in traces],[q['id'] for q in cases],method)

    def test_frozen_selection_and_fresh_test_have_full_trace_coverage(self):
        cases=load('benchmark/nd13/test.json'); selection=load('results/nd13/v2/selection.json')
        self.assertEqual(selection['selected'],'lexical')
        self.assertEqual(selection['dev_sha256'],digest('benchmark/nd13/dev.json'))
        self.assertEqual(selection['test_sha256'],digest('benchmark/nd13/test.json'))
        for method in ('baseline',selection['selected']):
            traces=load(f'results/nd13/v2/test/{method}/traces.json')
            self.assertEqual([t['query_id'] for t in traces],[q['id'] for q in cases],method)
            self.assertTrue(all(t['split']=='test' and t['answerable']==q['answerable'] for t,q in zip(traces,cases)))

if __name__=='__main__': unittest.main()
