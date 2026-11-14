"""Prepare the new Day 7 holdout BEFORE experiment selection; never reuse Day 6 test."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import load, save, utc


def main():
    root = Path(__file__).resolve().parents[1]
    if (root / 'results/selection.json').exists():
        raise ValueError('Cannot regenerate benchmark after selection; create a new experiment directory')
    chunks = load(root / 'data/day6/chunks.json')
    dev = [q for q in load(root / 'benchmark/dev.json') if q['answerable']]
    dev += [
        {'id': 'd-missing-1', 'split': 'dev', 'question': "On what exact date was Alice born?", 'answerable': False,
         'expected_behavior': 'search_and_abstain', 'absence_reason': 'The complete 82-unit story contains no birth date for Alice. Age-related dialogue is not a date of birth.'},
        {'id': 'd-missing-2', 'split': 'dev', 'question': "What is the White Rabbit’s annual salary in pounds?", 'answerable': False,
         'expected_behavior': 'search_and_abstain', 'absence_reason': 'Rabbit scenes mention errands and a court role, but the full story specifies no annual salary or salary amount.'},
    ]
    specs = [
        ('t01', 'What did the White Rabbit take out of its waistcoat-pocket?', 'A watch.', 1,
         'took a watch out of its waistcoat-pocket', {}),
        ('t02', 'What name did the White Rabbit call Alice when mistaking her for his housemaid?', 'Mary Ann.', 18,
         'Why, Mary Ann, what _are_ you doing out here?', {}),
        ('t03', 'What did the Caterpillar take out of its mouth before addressing Alice?', 'A hookah.', 26,
         'the Caterpillar took the hookah out of its mouth', {}),
        ('t04', 'In chapter VIII, why were the gardeners painting the white roses red?',
         'They had planted a white rose-tree instead of a red one and feared beheading if the Queen found out.', 48,
         'this here ought to have been a _red_ rose-tree, and we put a white one in by mistake; and if the Queen was to find it out, we should all have our heads cut off', {'chapter': 'VIII'}),
        ('t05', 'In chapter XI, what did the White Rabbit hold in each hand near the King at the trial?',
         'A trumpet in one hand and a scroll of parchment in the other.', 70,
         'the White Rabbit, with a trumpet in one hand, and a scroll of parchment in the other', {'chapter': 'XI'}),
    ]
    test = []
    for cid, question, expected, page, evidence, filters in specs:
        assert any(c['page'] == page and evidence in c['text'] for c in chunks), cid
        test.append({'id': cid, 'split': 'test', 'question': question, 'answerable': True,
                     'expected_answer': expected, 'gold': [{'source_id': 'alice', 'page': page, 'evidence': evidence}], 'filter': filters})
    test += [
        {'id': 't-missing-1', 'split': 'test', 'question': 'How many pounds did the gardeners pay for the red paint used on the roses?',
         'answerable': False, 'expected_behavior': 'search_and_abstain',
         'absence_reason': 'Read the full rose-tree and gardener scenes and searched all 82 units: no purchase price for paint is specified.'},
        {'id': 't-missing-2', 'split': 'test', 'question': "What is the Hatter’s street number and postal code?",
         'answerable': False, 'expected_behavior': 'search_and_abstain',
         'absence_reason': 'Read the full tea-party and Hatter scenes and searched all 82 units: no street number or postal code is specified.'},
    ]
    save(root / 'benchmark/dev.json', dev)
    save(root / 'benchmark/test.json', test)
    save(root / 'benchmark/protocol.json', {
        'created_at': utc(), 'dev': {'answerable': 15, 'unanswerable': 2}, 'test': {'answerable': 5, 'unanswerable': 2},
        'origin': 'Reuse Day 6 dev only. Five new answerable test questions and four new absence questions authored before Day 7 tuning.',
        'absence_audit': 'Author checked full corpus topic occurrences and all relevant scenes, not merely top-k output. AI-authored labels; student should audit.',
        'selection': 'Maximize dev grounded-answer mean (errors receive zero for selection), then correct abstention rate, then context evidence rate, then lower median latency, then config name.',
        'retrieval_hit': 'Exact gold evidence in a single chunk at the gold source and logical page. Gold items are alternatives. No multi-hop cases.',
        'context_grade': '0: missing evidence; 1: partial evidence/conditions/source; 2: complete evidence and source. AI-assisted manual reading with reasons, not a semantic verifier score.',
        'answer_grade': '0: incorrect, unsupported, abstained, or error; 1: partially correct and supported; 2: complete, correct, supported by citations.',
        'gold_isolation': 'Only question, explicit filter, configuration enter agent/retriever. Metrics are computed after generation.',
        'filter_policy': 'Only chapter explicitly named in the user question; no gold-derived filters. Same filters for every method.',
        'cost': 'Ollama and FastEmbed local: service cost USD 0; GPU/CPU/electricity not priced. Token and wall-time totals retained.',
    })
    print('Prepared 17 dev + 7 new test questions.')


if __name__ == '__main__':
    main()
