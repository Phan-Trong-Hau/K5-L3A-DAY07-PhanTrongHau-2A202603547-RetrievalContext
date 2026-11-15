"""Protocol and ranking regressions; mocks here are never benchmark results."""
import unittest

from src.agent import run_agent, validate_answer
from src.agent_v2 import normalize_final
from src.retrieval import Retriever, mmr
from test_solution import Provider, Store, chunk


class MMRTests(unittest.TestCase):
    def test_diversifies_similar_dense_candidates(self):
        rows = [{**chunk('a', 'one'), 'score': 1.0}, {**chunk('b', 'duplicate'), 'score': .99},
                {**chunk('c', 'different'), 'score': .8}]
        vectors = {'a': [1., 0.], 'b': [1., 0.], 'c': [0., 1.]}
        self.assertEqual([r['id'] for r in mmr(rows, vectors, 2)], ['a', 'c'])
        self.assertEqual([r['id'] for r in mmr(rows, vectors, 2, weight=1)], ['a', 'b'])

    def test_rejects_zero_vector_and_bad_weight(self):
        with self.assertRaises(ValueError):
            mmr([{**chunk('a', 'one'), 'score': 1}], {'a': [0, 0]}, 1)
        with self.assertRaises(ValueError):
            mmr([], {}, 1, weight=0)

    def test_cross_encoder_overrides_fusion_ranking_and_caches_scores(self):
        class Scorer:
            def __init__(self): self.calls = 0
            def rerank(self, query, documents, batch_size):
                self.calls += 1
                assert query == 'question' and len(documents) == 2
                return [.1, .9]
        class FakeStore(Retriever):
            def search(self, query, *, filters=None, top_k=3, method='dense', candidates=20):
                if method in ('dense', 'bm25'):
                    self.observed_filters.append(filters)
                    return [{**chunk('a', 'first'), 'score': .8}, {**chunk('b', 'second'), 'score': .7}][:top_k]
                return super().search(query, filters=filters, top_k=top_k, method=method, candidates=candidates)
        retriever = FakeStore.__new__(FakeStore)
        retriever.reranker, retriever.rerank_cache, retriever.observed_filters = Scorer(), {}, []
        for _ in range(2):
            result = retriever.search('question', method='rerank', filters={'chapter': 'I'}, top_k=1)
            self.assertEqual(result[0]['id'], 'b')
            self.assertEqual(result[0]['score'], .9)
            self.assertIn('fusion_score', result[0])
        self.assertEqual(retriever.reranker.calls, 1)
        self.assertTrue(all(f == {'chapter': 'I'} for f in retriever.observed_filters))


class AgentV2Tests(unittest.TestCase):
    config = {'method': 'dense', 'top_k': 3, 'max_searches': 1, 'budget': 500, 'policy_v2': True}

    def test_textual_tool_json_and_spaced_citations(self):
        action = normalize_final({'content': 'submit_answer({"status":"answered","answer":"Seven [C1].","citations":["C1"]})'})
        self.assertEqual(action['answer'], 'Seven [C1].')
        self.assertEqual(normalize_final({'content': 'Seven [ C1 ].'})['citations'], ['C1'])
        with self.assertRaises(ValueError):
            normalize_final({'content': 'submit_answer({__import__("os"): 1})'})

    def test_echoed_header_and_bare_citation(self):
        action = normalize_final({'content': '[ C1 | tài liệu | page 77 ] 4,8% [C1]'})
        self.assertTrue(validate_answer(action, ['C1']))
        self.assertIn('4,8%', action['answer'])
        self.assertFalse(validate_answer(normalize_final({'content': '[C1]'}), ['C1']))

    def test_citation_alias_expands_to_original_id(self):
        provider = Provider([('search_documents', {'query': 'rewritten'}),
                             ('submit_answer', {'status': 'answered', 'answer': 'Seven days [C1].', 'citations': ['C1']})])
        trace = run_agent('Original question?', provider, Store(), self.config)
        self.assertEqual(trace['status'], 'answered')
        self.assertEqual(trace['citations'], ['a'])
        self.assertEqual(trace['answer'], 'Seven days [a].')
        self.assertEqual(trace['citation_map'], {'C1': 'a'})
        self.assertIn('[C1 |', trace['context'])
        event = next(e for e in trace['events'] if e['event'] == 'search')
        self.assertEqual(event['query'], 'Original question?')
        self.assertEqual(event['model_query'], 'rewritten')

    def test_premature_refusal_requires_real_search_and_new_model_decision(self):
        provider = Provider([('submit_answer', {'status': 'abstain', 'answer': 'No evidence.', 'citations': []}),
                             ('search_documents', {'query': 'q'}),
                             ('submit_answer', {'status': 'abstain', 'answer': 'No evidence after search.', 'citations': []})])
        trace = run_agent('q', provider, Store(), self.config)
        self.assertEqual(trace['status'], 'abstain')
        self.assertEqual(sum(e['event'] == 'search' for e in trace['events']), 1)
        self.assertEqual(trace['usage']['model_calls'], 3)
        self.assertTrue(any(e.get('reason') == 'retrieval_required' for e in trace['events']))

    def test_repeated_skip_runs_retrieval_fallback_before_abstaining(self):
        provider = Provider([('submit_answer', {'status': 'abstain', 'answer': 'No evidence.', 'citations': []})]*2)
        trace = run_agent('q', provider, Store(), self.config)
        self.assertEqual(trace['status'], 'abstain')
        self.assertEqual(sum(e['event'] == 'search' for e in trace['events']), 1)
        self.assertEqual(trace['events'][-1]['reason'], 'model_repeated_protocol_violation')

    def test_citation_format_repair_is_bounded(self):
        provider = Provider([('search_documents', {'query': 'q'}),
                             ('submit_answer', {'status': 'answered', 'answer': 'Seven [fake].', 'citations': ['fake']}),
                             ('submit_answer', {'status': 'answered', 'answer': 'Seven [C1].', 'citations': ['C1']})])
        trace = run_agent('q', provider, Store(), self.config)
        self.assertEqual(trace['status'], 'answered')
        self.assertIn('citation_format', [e.get('reason') for e in trace['events']])

    def test_provider_error_preserves_context(self):
        class Offline(Provider):
            def chat(self, messages, tools):
                if self.messages:
                    raise ConnectionError('offline')
                return super().chat(messages, tools)
        trace = run_agent('q', Offline([('search_documents', {'query': 'q'})]), Store(), self.config)
        self.assertEqual(trace['status'], 'error')
        self.assertTrue(trace['context_ids'])


if __name__ == '__main__':
    unittest.main()
