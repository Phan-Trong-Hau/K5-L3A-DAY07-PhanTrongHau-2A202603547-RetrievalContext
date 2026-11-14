"""Record independent, source-grounded manual labels for the frozen ND13 test."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.common import load, save, utc
from scripts.freeze import audit

REVIEWER='Codex — AI-assisted manual review against frozen gold and cited OCR passages; student confirmation pending.'
LABELS={
 'baseline': {
  'nd13-21':(0,0,'Abstained on an answerable case; no gold passage in context.'),
  'nd13-22':(0,0,'Abstained on an answerable case; no gold passage in context.'),
  'nd13-23':(0,0,'Gold was in original top-3 but omitted from final context; abstention is incorrect.'),
  'nd13-24':(2,2,'Correct 72-hour answer; cited passage on page 13 supports it.'),
  'nd13-25':(0,0,'Runtime protocol error; no final evidence context.'),
 },
 'lexical': {
  'nd13-21':(2,2,'Correct 72-hour limit and legal exception; cited page 8 passage supports answer.'),
  'nd13-22':(2,2,'Names all four parties and the requirement to request related parties stop; cited passage supports answer.'),
  'nd13-23':(1,2,'Answer states the right condition and gold is present in context, but its citation resolves to page 15 and does not support the claim on page 11.'),
  'nd13-24':(2,2,'Correct 72-hour deadline and triggering request; cited page 13 passage supports answer.'),
  'nd13-25':(0,0,'Independent evaluation of the original query ranking found the page 21 evidence, but the agent tool loop skipped mandatory retrieval and ended in protocol error; final context is empty.'),
 }
}

def main():
 cases=load('benchmark/nd13/test.json'); byid={q['id']:q for q in cases}
 for method,labels in LABELS.items():
  traces=load(f'results/nd13/v2/test/{method}/traces.json'); reviews=[]
  for t in traces:
   q=byid[t['query_id']]
   citation_support=[]
   for cid in t['citations']:
    cid=t.get('citation_map',{}).get(cid,cid)
    chunk=next((c for c in t.get('original_query_results',[]) if c['id']==cid),None)
    if chunk is None:
     chunks=load('data/nd13/chunks.json'); chunk=next((c for c in chunks if c['id']==cid),None)
    citation_support.append(bool(chunk and any(g['source_id']==chunk['source_id'] and g['page']==chunk['page'] for g in q.get('gold',[]))))
   entry={'query_id':q['id'],'reviewer':REVIEWER,'reviewed_at':utc(),'citation_support':citation_support}
   if q['answerable']:
    grade,context,reason=labels[q['id']]
    entry.update(answer_grade=grade,context_grade=context,reason=reason)
   else:
    entry.update(abstention_correct=t['status']=='abstain',reason='Không có yêu cầu trong tài liệu; câu trả lời đúng là từ chối kèm diễn giải thiếu bằng chứng.' if t['status']=='abstain' else 'Không từ chối câu hỏi không có bằng chứng.')
   reviews.append(entry)
  folder=Path(f'results/nd13/v2/test/{method}')
  save(folder/'reviews.json',reviews)
  audited=audit(cases,traces,reviews); save(folder/'audit_summary.json',audited)
  from src.evaluation import summarize
  save(folder/'summary.json',{**summarize(traces),**audited})
  print(method,audited)
 comparison={m:load(f'results/nd13/v2/test/{m}/summary.json') for m in LABELS}
 save('results/nd13/v2/test/comparison.json',comparison)

if __name__=='__main__': main()
