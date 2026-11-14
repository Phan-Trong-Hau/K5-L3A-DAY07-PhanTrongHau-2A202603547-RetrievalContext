"""Offline behavior tests. Fake provider output here is never benchmark evidence."""
import unittest
from pathlib import Path

from src.agent import final_action, pack_context, run_agent, validate_answer
from src.common import load, sha256
from src.evaluation import hit, summarize, validate_cases
from src.retrieval import BM25, rrf

ROOT = Path(__file__).resolve().parents[1]


def chunk(cid, text, chapter='I', page=1):
    return {'id': cid, 'text': text, 'source_id': 'alice', 'source': 'book.txt',
            'page': page, 'metadata': {'chapter': chapter, 'language': 'en'}}


class RetrievalTests(unittest.TestCase):
    def test_bm25_filter_is_applied_before_top_k(self):
        index = BM25([chunk('a', 'watch watch watch'), chunk('b', 'watch rabbit', chapter='II')])
        self.assertEqual(index.search('watch', filters={'chapter': 'II'}, top_k=1)[0]['id'], 'b')
        self.assertEqual(index.search('不存在'), [])

    def test_rrf_uses_ranks_not_incompatible_raw_scores(self):
        a, b, c = chunk('a', 'one'), chunk('b', 'two'), chunk('c', 'three')
        result = rrf({'dense': [{**a, 'score': .9}, {**b, 'score': .8}],
                      'bm25': [{**b, 'score': 999}, {**c, 'score': 998}]}, 3)
        self.assertEqual(result[0]['id'], 'b')
        self.assertAlmostEqual(result[0]['score'], 1/61 + 1/62)

    def test_context_dedup_budget_and_whole_chunks(self):
        a, b = chunk('a', 'x' * 60), chunk('b', 'support')
        text, ids = pack_context([[a, b], [b]], 100)
        self.assertEqual(ids, ['b'])
        self.assertLessEqual(len(text), 100)
        self.assertEqual(text.count('[b |'), 1)
        self.assertEqual(pack_context([[a]], 1), ('', []))

    def test_snapshot_and_benchmark_contract(self):
        data = ROOT / 'data/day6'
        manifest = load(data / 'provenance.json')
        for name, expected in manifest['sha256'].items():
            self.assertEqual(sha256(data / name), expected, name)
        chunks, vectors = load(data / 'chunks.json'), load(data / 'vectors.json')
        self.assertEqual([c['id'] for c in chunks], [v['id'] for v in vectors])
        self.assertTrue(all(len(v['vector']) == 384 for v in vectors))
        self.assertGreaterEqual(len({c['page'] for c in chunks}), 30)
        for split, required in [('dev', (15, 2)), ('test', (5, 2))]:
            cases = load(ROOT / f'benchmark/{split}.json')
            validate_cases(chunks, cases, split)
            self.assertGreaterEqual(sum(q['answerable'] for q in cases), required[0])
            self.assertGreaterEqual(sum(not q['answerable'] for q in cases), required[1])


class Provider:
    def __init__(self, actions):
        self.actions = iter(actions)
        self.messages = []

    def chat(self, messages, tools):
        self.messages.append(messages)
        name, args = next(self.actions)
        return {'done': True, 'message': {'role': 'assistant', 'content': '', 'tool_calls': [
            {'function': {'name': name, 'arguments': args}}]}, 'prompt_eval_count': 5, 'eval_count': 3}


class Store:
    def search(self, query, **kwargs):
        return [chunk('a', 'Seven days.')]


class AgentBehaviorTests(unittest.TestCase):
    config = {'method': 'dense', 'budget': 500, 'max_searches': 1, 'top_k': 3}

    def test_native_tool_loop_and_usage(self):
        p = Provider([('search_documents', {'query': 'refund'}), ('submit_answer', {
            'status': 'answered', 'answer': 'Seven days [a].', 'citations': ['a']})])
        trace = run_agent('How long?', p, Store(), self.config)
        self.assertEqual(trace['status'], 'answered')
        self.assertEqual(trace['context_ids'], ['a'])
        self.assertEqual(trace['usage'], {'prompt_tokens': 10, 'completion_tokens': 6, 'model_calls': 2})
        self.assertNotIn('gold', str(p.messages))

    def test_bad_citation_is_error_not_successful_abstention(self):
        p = Provider([('search_documents', {'query': 'refund'}), ('submit_answer', {
            'status': 'answered', 'answer': 'Seven days [fake].', 'citations': ['fake']})])
        trace = run_agent('How long?', p, Store(), self.config)
        self.assertEqual(trace['status'], 'error')
        self.assertIn('citation', trace['error'])
        self.assertTrue(trace['context'])

    def test_provider_error_keeps_prior_search(self):
        class Broken(Provider):
            def chat(self, messages, tools):
                if self.messages:
                    raise ConnectionError('offline')
                return super().chat(messages, tools)
        trace = run_agent('q', Broken([('search_documents', {'query': 'q'})]), Store(), self.config)
        self.assertEqual(trace['status'], 'error')
        self.assertTrue(any(e['event'] == 'search' for e in trace['events']))

    def test_cannot_finish_without_search_or_unknown_inline_citation(self):
        p = Provider([('submit_answer', {'status': 'abstain', 'answer': 'No evidence.', 'citations': []})])
        self.assertEqual(run_agent('q', p, Store(), self.config)['status'], 'error')
        self.assertFalse(validate_answer({'status': 'answered', 'answer': 'x [a] [b]', 'citations': ['a']}, ['a']))

    def test_plain_final_text_and_explicit_abstention(self):
        self.assertEqual(final_action({'content': 'Seven days [a].'})['citations'], ['a'])
        self.assertEqual(final_action({'content': 'ABSTAIN: no date in context.'})['status'], 'abstain')
        refusal = final_action({'content': 'ABSTAIN: no date [a].'})
        self.assertEqual(refusal['answer'], 'ABSTAIN: no date.')
        self.assertEqual(refusal['citations'], [])
        # Missing citations alone must not be relabelled as a correct refusal.
        self.assertEqual(final_action({'content': 'A made-up date.'})['status'], 'answered')

    def test_search_limit_allows_final_answer_without_executing_extra_search(self):
        p = Provider([('search_documents', {'query': 'first'}), ('search_documents', {'query': 'second'}),
                      ('submit_answer', {'status': 'abstain', 'answer': 'No evidence.', 'citations': []})])
        trace = run_agent('q', p, Store(), self.config)
        self.assertEqual(trace['status'], 'abstain')
        self.assertEqual(sum(e['event'] == 'search' for e in trace['events']), 1)

    def test_evidence_checks_page_and_source(self):
        self.assertFalse(hit(chunk('a', 'Seven days.', page=2), [
            {'source_id': 'alice', 'page': 1, 'evidence': 'Seven days.'}]))


if __name__ == '__main__':
    unittest.main()
