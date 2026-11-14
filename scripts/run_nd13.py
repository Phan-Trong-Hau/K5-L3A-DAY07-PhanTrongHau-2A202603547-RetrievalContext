"""Run all five Day 7 retrieval+agent configurations on the frozen Vietnamese ND 13 cases."""
import importlib.metadata, json, platform, urllib.request, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.agent import Ollama, run_agent
from src.common import load, save, sha256, utc
from src.evaluation import hit, summarize, validate_cases
from src.retrieval import Retriever

def main():
    source=load('benchmark/nd13_questions_source.json')
    cases=[]
    for q in source:
        cases.append({'id':q['id'],'split':'test','question':q['question'],'filter':q.get('filter') or {},
            'answerable':True,'expected_answer':q['expected_answer'],
            'gold':[{'source_id':q['gold_source_id'],'page':q['gold_page'],'evidence':q['evidence_quote']}],
            'absence_reason':None,'kind':q.get('kind'),'note':q.get('note')})
    save('benchmark/nd13/test.json',cases)
    configs=load('configs/experiments.json'); output=Path('results/nd13')
    model='qwen3:4b-instruct'; url='http://localhost:11434'
    provider=Ollama(model=model,url=url,context_size=4096)
    with urllib.request.urlopen(url+'/api/tags',timeout=10) as response: tags=json.load(response)
    tag=next(m for m in tags['models'] if m['name']==model)
    retriever=Retriever(data='data/nd13',store='.qdrant_nd13')
    try:
        validate_cases(retriever.chunks,cases,'test')
        for name,base_config in configs.items():
            config={**base_config,'language':'vi','document_title':'Nghị định số 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân'}
            out=output/'test'/name; out.mkdir(parents=True,exist_ok=True)
            manifest={'model':model,'model_digest':tag['digest'],'config':config,'context_window':4096,
                'benchmark_sha256':sha256('benchmark/nd13/test.json'),'corpus_sha256':sha256('data/nd13/provenance.json'),
                'code_sha256':{str(p):sha256(p) for p in sorted(Path('src').glob('*.py'))}}
            mp=out/'manifest.json'; tp=out/'traces.json'
            if tp.exists() and load(mp)!=manifest: raise ValueError(f'Cannot resume changed run: {out}')
            traces=load(tp) if tp.exists() else []; done={t['query_id'] for t in traces}
            if not done<={q['id'] for q in cases} or len(done)!=len(traces): raise ValueError('Invalid existing traces')
            save(mp,manifest)
            for q in cases:
                if q['id'] in done: continue
                trace=run_agent(q['question'],provider,retriever,config,filters=q.get('filter'))
                trace.update(query_id=q['id'],split='test',configuration=name,config=config,answerable=True)
                try:
                    ranking=retriever.search(q['question'],filters=q.get('filter'),top_k=3,method=config['method'],candidates=config.get('candidates',20))
                    trace['original_query_results']=ranking
                    trace['hit1']=bool(ranking and hit(ranking[0],q['gold']))
                    trace['hit3']=any(hit(c,q['gold']) for c in ranking)
                    trace['context_hit']=any(hit(c,q['gold']) for c in retriever.chunks if c['id'] in trace['context_ids'])
                except Exception as exc:
                    trace.update(status='error',evaluation_error=f'{type(exc).__name__}: {exc}',hit1=False,hit3=False,context_hit=False)
                traces.append(trace); save(tp,traces); save(out/'summary.json',summarize(traces))
                print(f"{name}/{q['id']}: {trace['status']} | hit3={trace.get('hit3')} context={trace.get('context_hit')} | {trace['elapsed_seconds']:.1f}s | {trace['answer']}",flush=True)
            reranker_snapshot=None
            if config['method']=='rerank' and retriever.reranker is not None:
                model_dir=Path(retriever.reranker.model._model_dir)
                reranker_snapshot={'model':'Xenova/ms-marco-MiniLM-L-6-v2','revision':model_dir.name,
                    'files':{str(p.relative_to(model_dir)):sha256(p) for p in model_dir.rglob('*') if p.is_file()}}
            save(out/'environment.json',{'recorded_at':utc(),'python':platform.python_version(),
                'versions':{p:importlib.metadata.version(p) for p in ['fastembed','qdrant-client','onnxruntime','numpy']},
                'ollama_tag':tag,'reranker_snapshot':reranker_snapshot,'cost_note':'Local inference; service cost USD 0.'})
    finally: retriever.close()
    print('All five ND13 configurations finished. Metrics are retrieval/context evidence only; answer quality needs per-case review.')

if __name__=='__main__': main()
