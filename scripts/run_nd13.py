"""Run the frozen ND13 dev set, then baseline + dev-selected config on the new test set."""
import argparse, importlib.metadata, json, platform, urllib.request
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.agent import Ollama, run_agent
from src.common import load, save, sha256, utc
from src.evaluation import hit, summarize, validate_cases
from src.retrieval import Retriever

METHODS=('baseline','lexical','hybrid','mmr','rerank')
CORE_FILES=('src/agent.py','src/agent_v2.py','src/common.py','src/evaluation.py','src/retrieval.py')


def make_manifest(name, config, model, digest, split):
    return {'model':model,'model_digest':digest,'config':config,'context_window':4096,
      'benchmark_sha256':sha256(f'benchmark/nd13/{split}.json'),
      'corpus_sha256':sha256('data/nd13/provenance.json'),
      'code_sha256':{p:sha256(p) for p in CORE_FILES},
      'runner':'scripts/run_nd13.py','selection_stage':split,'method':name}


def run(split):
    configs=load('configs/experiments.json'); out_root=Path('results/nd13/v2')
    cases=load(f'benchmark/nd13/{split}.json')
    selection=None
    if split=='test':
        selection=load(out_root/'selection.json')
        if selection['dev_sha256']!=sha256('benchmark/nd13/dev.json') or selection['test_sha256']!=sha256('benchmark/nd13/test.json'):
            raise ValueError('Dev/test benchmark changed after selection freeze')
        if selection['config_sha256']!=sha256('configs/experiments.json'):
            raise ValueError('Configs changed after dev selection')
        for path,digest in selection['code_sha256'].items():
            if sha256(path)!=digest: raise ValueError(f'Core code changed after freeze: {path}')
        names=list(dict.fromkeys(['baseline',selection['selected']]))
    else:
        if (out_root/'selection.json').exists(): raise ValueError('Dev is frozen; start a new version to tune')
        names=list(METHODS)
    provider=Ollama(model='qwen3:4b-instruct',url='http://localhost:11434',context_size=4096)
    with urllib.request.urlopen('http://localhost:11434/api/tags',timeout=10) as response: tags=json.load(response)
    tag=next((m for m in tags['models'] if m['name']=='qwen3:4b-instruct'),None)
    if not tag: raise ValueError('Qwen model is not installed')
    if selection and tag['digest']!=selection['model_digest']: raise ValueError('Model changed after freeze')
    retriever=Retriever(data='data/nd13',store='.qdrant_nd13')
    try:
        validate_cases(retriever.chunks,cases,split)
        for name in names:
            config={**configs[name],'language':'vi','document_title':'Nghị định số 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân'}
            out=out_root/split/name; out.mkdir(parents=True,exist_ok=True)
            path=out/'traces.json'; manifest=make_manifest(name,config,tag['name'],tag['digest'],split)
            manifest_path=out/'manifest.json'
            traces=load(path) if path.exists() else []
            if traces:
                if manifest_path.exists():
                    if load(manifest_path)!=manifest: raise ValueError(f'Cannot resume changed run: {out}')
                elif not all(t.get('trace_origin') for t in traces):
                    raise ValueError(f'Unmanifested traces are not eligible for resume: {out}')
                elif any(t.get('config')!=config for t in traces):
                    raise ValueError(f'Imported trace configuration mismatch: {out}')
            save(manifest_path,manifest)
            done={t['query_id'] for t in traces}
            if not done<={q['id'] for q in cases} or len(done)!=len(traces): raise ValueError('Invalid existing trace IDs')
            if traces: save(out/'summary.json',summarize(traces))
            for q in cases:
                if q['id'] in done: continue
                trace=run_agent(q['question'],provider,retriever,config,filters=q.get('filter'))
                trace.update(query_id=q['id'],split=split,configuration=name,config=config,answerable=q['answerable'])
                try:
                    ranking=retriever.search(q['question'],filters=q.get('filter'),top_k=3,method=config['method'],candidates=config.get('candidates',20))
                    trace['original_query_results']=ranking
                    gold=q.get('gold',[])
                    trace['hit1']=bool(ranking and hit(ranking[0],gold)) if q['answerable'] else None
                    trace['hit3']=any(hit(c,gold) for c in ranking) if q['answerable'] else None
                    trace['context_hit']=any(hit(c,gold) for c in retriever.chunks if c['id'] in trace['context_ids']) if q['answerable'] else None
                except Exception as exc:
                    trace.update(status='error',evaluation_error=f'{type(exc).__name__}: {exc}',hit1=False,hit3=False,context_hit=False)
                traces.append(trace); done.add(q['id'])
                save(path,traces); save(out/'summary.json',summarize(traces))
                print(f"{split}/{name}/{q['id']}: {trace['status']} | hit3={trace.get('hit3')} context={trace.get('context_hit')} | {trace['elapsed_seconds']:.1f}s | {trace['answer']}",flush=True)
            reranker_snapshot=None
            if config['method']=='rerank' and retriever.reranker is not None:
                model_dir=Path(retriever.reranker.model._model_dir)
                reranker_snapshot={'model':'Xenova/ms-marco-MiniLM-L-6-v2','revision':model_dir.name,
                  'files':{str(p.relative_to(model_dir)):sha256(p) for p in model_dir.rglob('*') if p.is_file()}}
            save(out/'environment.json',{'recorded_at':utc(),'python':platform.python_version(),
              'versions':{p:importlib.metadata.version(p) for p in ['fastembed','qdrant-client','onnxruntime','numpy']},
              'ollama_tag':tag,'reranker_snapshot':reranker_snapshot,
              'cost_note':'Local inference; service cost USD 0, electricity/hardware not priced.'})
    finally: retriever.close()


def main():
    p=argparse.ArgumentParser(); p.add_argument('--split',choices=['dev','test'],required=True)
    run(p.parse_args().split)

if __name__=='__main__': main()
