import unittest

from scripts.freeze import audit


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.cases = [{'id': 'q', 'answerable': True}]
        self.trace = {'query_id': 'q', 'status': 'answered', 'citations': ['x'], 'context_ids': ['x']}
        self.review = {'query_id': 'q', 'reviewer': 'unit test', 'reason': 'test fixture',
                       'answer_grade': 2, 'context_grade': 2, 'citation_support': [True]}

    def test_error_is_zero_and_remains_in_all_answerable_denominators(self):
        cases = self.cases + [{'id': 'broken', 'answerable': True}]
        traces = [self.trace, {'query_id': 'broken', 'status': 'error', 'citations': [], 'context_ids': []}]
        error_review = {'query_id': 'broken', 'reviewer': 'unit test', 'reason': 'runtime error',
                        'answer_grade': 0, 'context_grade': 2, 'citation_support': []}
        stats = audit(cases, traces, [self.review, error_review])
        self.assertEqual(stats['errors'], 1)
        self.assertEqual(stats['grounded_mean'], 1)
        self.assertEqual(stats['selection_mean_errors_zero'], 1)
        self.assertEqual(stats['answer_grades']['0'], 1)
        self.assertEqual(stats['context_grades']['2'], 2)
        self.assertEqual(stats['false_abstention'], {'n': 0, 'N': 2, 'rate': 0})

    def test_error_on_missing_evidence_is_not_a_correct_abstention(self):
        case = {'id': 'missing', 'answerable': False}
        trace = {'query_id': 'missing', 'status': 'error', 'citations': [], 'context_ids': []}
        review = {'query_id': 'missing', 'reviewer': 'unit test', 'reason': 'runtime error',
                  'abstention_correct': False, 'citation_support': []}
        stats = audit([case], [trace], [review])
        self.assertEqual(stats['abstention'], {'n': 0, 'N': 1, 'rate': 0})

    def test_missing_review_rejected(self):
        with self.assertRaises(ValueError):
            audit(self.cases, [self.trace], [])

    def test_review_cannot_validate_a_citation_outside_context(self):
        stats = audit(self.cases, [{**self.trace, 'context_ids': []}], [self.review])
        self.assertEqual(stats['citation_support']['n'], 0)

    def test_false_abstention_cannot_receive_full_answer_grade(self):
        with self.assertRaises(ValueError):
            audit(self.cases, [{**self.trace, 'status': 'abstain'}], [self.review])


if __name__ == '__main__':
    unittest.main()
