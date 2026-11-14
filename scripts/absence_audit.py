"""Record a full-corpus keyword/topic scan; this is NOT a top-k absence classifier."""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import load, save, sha256


def main():
    pages = load('data/day6/pages.json')
    specifications = [
        ('d-missing-1', ['born', 'birth', 'birthday'],
         'Only birthday occurrence is a general thought about birthday presents on p58; it specifies no date of birth for Alice.'),
        ('d-missing-2', ['salary', 'wages', 'pounds', 'paid', 'Rabbit'],
         'No salary/wages/paid; the hundred pounds at p12 is an estimate of the value of a farmer’s dog, unrelated to the Rabbit’s salary.'),
        ('t-missing-1', ['paint', 'price', 'cost', 'pounds'],
         'All paint occurrences are on p48 describing painting roses, not purchase or price. The pounds occurrence is about a dog at p12; cost at p59 refers to lives.'),
        ('t-missing-2', ['Hatter', 'street', 'postal', 'postcode', 'address'],
         'The Cat points toward a Hatter’s home on p39. Tea-party/court passages give no street number or postal code; address matches are verbs addressed/addressing.'),
    ]
    audit = []
    for cid, terms, decision in specifications:
        hits = {term: [{'page': page['page'], 'excerpt': m.group(0)} for page in pages
                       for m in re.finditer(r'.{0,70}' + re.escape(term) + r'.{0,100}', page['text'], re.I)] for term in terms}
        audit.append({'query_id': cid, 'scope': 'All 82 logical units, plus source-scene reading',
                      'pages_sha256': sha256('data/day6/pages.json'), 'topic_scan': hits,
                      'decision': decision, 'reviewer': 'Codex — AI-assisted source review; student confirmation pending'})
    save('benchmark/absence_audit.json', audit)


if __name__ == '__main__':
    main()
