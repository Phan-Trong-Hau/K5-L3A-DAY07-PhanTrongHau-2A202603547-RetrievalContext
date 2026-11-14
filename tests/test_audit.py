import unittest

from scripts.freeze import audit


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.cases = [{'id': 'q', 'answerable': True}]
        self.trace = {'query_id': 'q', 'status': 'answered', 'citations': ['x'], 'context_ids': ['x']}
        self.review = {'query_id': 'q', 'reviewer': 'unit test', 'reason': 'test fixture',
                       'answer_grade': 2, 'context_grade': 2, 'citation_support': [True]}

    def test_error_penalized_for_selection_and_not_hidden_in_quality(self):
        cases = self.cases + [{'id': 'broken', 'answerable': True}]
        traces = [self.trace, {'query_id': 'broken', 'status': 'error'}]
        stats = audit(cases, traces, [self.review])
        self.assertEqual(stats['errors'], 1)
        self.assertEqual(stats['grounded_mean'], 2)
        self.assertEqual(stats['selection_mean_errors_zero'], 1)

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
