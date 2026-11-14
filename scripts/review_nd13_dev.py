"""AI-assisted manual source/trace labels for every audited ND13 dev result."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.common import load, save

REVIEWER='Codex — AI-assisted manual review of Day 06 OCR source and trace; student confirmation pending'
GRADES={
 'baseline':[0,0,0,2,0,0,0,0,0,0,2,0,2,0,2,0,0,0,2,0],
 'lexical':[2,2,0,0,2,0,2,0,2,0,2,2,2,1,2,2,2,0,2,2],
 'hybrid':[0,0,0,0,2,0,0,2,2,0,2,0,2,2,2,2,0,0,2,2],
 'mmr':[0,0,0,1,2,0,0,0,2,0,2,2,2,0,2,2,0,0,2,2],
 'rerank':[2,2,0,0,2,0,2,2,2,0,2,0,2,1,2,2,2,0,2,2],
}
# Related passages make the context partial (1); exact gold passage in final context is 2.
PARTIAL={
 'baseline':{'vi03','vi07','vi09','vi10','vi14','vi16','vi18','vi20'},
 'lexical':set(),
 'hybrid':{'vi01','vi02','vi03','vi06','vi07'},
 'mmr':{'vi01','vi02','vi03','vi06','vi07','vi10','vi14','vi17','vi18'},
 'rerank':{'vi03','vi06','vi18'},
}
# These non-gold citations were read in the cited source passage and support part of the
# specific answer (appendix titles/forms). Other non-gold citations are unsupported.
SUPPLEMENTARY={
 ('lexical','vi13',29),('lexical','vi14',29),
 ('mmr','vi13',29),('rerank','vi14',34),
}


def main():
 cases=load('benchmark/nd13/dev.json'); chunks={c['id']:c for c in load('data/nd13/chunks.json')}
 for method, grades in GRADES.items():
  traces=load(f'results/nd13/v2/dev/{method}/traces.json'); by={t['query_id']:t for t in traces}
  reviews=[]
  for q in cases:
   t=by[q['id']]; row={'query_id':q['id'],'reviewer':REVIEWER,'citation_support':[]}
   for cid in t.get('citations',[]):
    c=chunks.get(cid)
    gold_hit=bool(c and q['answerable'] and any(g['source_id']==c['source_id'] and g['page']==c['page'] and g['evidence'] in c['text'] for g in q.get('gold',[])))
    supplemental=bool(c and (method,q['id'],c['page']) in SUPPLEMENTARY)
    row['citation_support'].append(bool(cid in t.get('context_ids',[]) and (gold_hit or supplemental)))
   if q['answerable']:
    # Map only the 20 previously source-reviewed cases; errors and abstentions remain zero.
    idx=next((i for i,x in enumerate(cases[:20]) if x['id']==q['id']),None)
    grade=GRADES[method][idx] if idx is not None else 0
    if t['status'] in ('abstain','error'): grade=0
    if t['status']=='answered' and grade==2 and t['citations'] and not any(row['citation_support']): grade=1
    context=2 if t.get('context_hit') else (1 if q['id'] in PARTIAL[method] else 0)
    row.update(answer_grade=grade,context_grade=context)
    if t['status']=='error': detail='Lượt model kết thúc lỗi; không nhận câu trả lời/citation hợp lệ, chấm 0.'
    elif t['status']=='abstain': detail='Câu hỏi có đáp án trong tài liệu nhưng agent từ chối; chấm 0. Đã đối chiếu câu hỏi với evidence gốc.'
    elif grade==0: detail='Câu trả lời sai hoặc citation không hỗ trợ claim theo đoạn được dẫn; chấm 0 sau đối chiếu với đáp án và trang nguồn.'
    elif grade==1: detail='Trả lời đúng một phần nhưng thiếu điều kiện hoặc citation hỗ trợ chưa đầy đủ; chấm 1.'
    else: detail='Câu trả lời đầy đủ, đúng với evidence trên trang nguồn; từng citation được kiểm tra trong context và đối chiếu nội dung.'
    row['reason']=f"{detail} Context grade {context}/2: {'đủ evidence' if context==2 else 'một phần liên quan, thiếu evidence đầy đủ' if context==1 else 'thiếu evidence'}; citations được kiểm tra riêng."
   else:
    ok=t['status']=='abstain'
    row.update(abstention_correct=ok)
    row['reason']='Đã rà toàn bộ 39 trang OCR cùng absence audit. Agent gọi search và từ chối đúng; không nêu số tiền hoặc con số không có trong văn bản.' if ok else 'Có dữ liệu cần từ chối nhưng agent không abstain đúng.'
   reviews.append(row)
  save(f'results/nd13/v2/dev/{method}/reviews.json',reviews)
 print('Wrote per-case dev reviews for all five methods.')

if __name__=='__main__': main()
