"""Import the already observed Day 06 external comparison as a transparent dev seed."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import load, save


def main():
    cases=load('benchmark/nd13/dev.json')
    ids={q['id'] for q in cases if q['answerable']}
    if len(ids)!=20: raise ValueError('Expected 20 previously evaluated answerable questions')
    for method in ('baseline','lexical','hybrid','mmr','rerank'):
        source=Path('results/nd13/external_v1')/method/'traces.json'
        dest=Path('results/nd13/v2/dev')/method/'traces.json'
        if dest.exists(): raise ValueError(f'Dev seed exists already: {dest}')
        traces=load(source)
        if {t['query_id'] for t in traces}!=ids: raise ValueError(f'Unexpected archived trace IDs for {method}')
        for trace in traces:
            trace['split']='dev'
            trace['trace_origin']=str(source)
            trace['development_reclassification']='Previously reported Day 06 external test; reclassified as development only. Not an independent holdout.'
        save(dest,traces)
    print('Imported 20 inspected cases per method as dev; original external_v1 traces remain unchanged.')

if __name__=='__main__': main()
