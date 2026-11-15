"""Offline checks of bonus caption selection and audit prerequisites."""
import unittest
from unittest.mock import patch

from scripts.bonus_pilot import PageRetriever
from scripts.run_bonus_v3 import run_v3
from src.retrieval import BM25


class BonusRetrieverTests(unittest.TestCase):
    def test_caption_preferred_over_reference(self):
        pages = [
            {'id': 'a', 'text': 'Bảng 2.2 được nhắc đến trong đoạn này. ' * 10, 'metadata': {}},
            {'id': 'b', 'text': 'BẢNG 2.2. Cơ cấu nền kinh tế\n2035: 27,1%', 'metadata': {}},
        ]
        retriever = PageRetriever.__new__(PageRetriever)
        retriever.bm25 = BM25(pages)
        result = retriever.search('Theo Bảng 2.2, năm 2035?', filters=None, top_k=1,
                                  method='bm25_caption', candidates=20)
        self.assertEqual(result[0]['id'], 'b')

    def test_no_caption_is_required_for_general_query(self):
        pages = [{'id': 'a', 'text': 'Tăng trưởng kinh tế Việt Nam', 'metadata': {}}]
        retriever = PageRetriever.__new__(PageRetriever)
        retriever.bm25 = BM25(pages)
        result = retriever.search('kinh tế', filters=None, top_k=1,
                                  method='bm25_caption', candidates=20)
        self.assertEqual(result[0]['id'], 'a')

    def test_multi_hop_conjunction_keeps_both_labelled_pages(self):
        pages = [
            {'id': 'a', 'text': 'BẢNG 2.1. Việc làm năm 2035', 'metadata': {}},
            {'id': 'b', 'text': 'BẢNG 2.2. Tiêu dùng năm 2035', 'metadata': {}},
            {'id': 'c', 'text': 'Việc làm và tiêu dùng năm 2035 ' * 8, 'metadata': {}},
        ]
        retriever = PageRetriever.__new__(PageRetriever)
        retriever.bm25 = BM25(pages)
        result = retriever.search('Bảng 2.1 và 2.2, năm 2035?', filters=None, top_k=2,
                                  method='bm25_caption', candidates=20)
        self.assertEqual({row['id'] for row in result}, {'a', 'b'})

    def test_abstention_cannot_add_unsupported_details(self):
        raw = {'status': 'abstain', 'answer': 'ABSTAIN: Unknown. Invented detail.',
               'citations': [], 'events': []}
        with patch('scripts.run_bonus_v3.run_agent', return_value=raw):
            result = run_v3('question', None, None, {})
        self.assertNotIn('Invented detail', result['answer'])
        self.assertIn('Invented detail', result['events'][-1]['original'])


if __name__ == '__main__':
    unittest.main()
