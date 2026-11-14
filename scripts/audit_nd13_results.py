"""Recompute metrics from frozen ND13 v2 traces without changing runs or selection."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from scripts.freeze import audit
from src.common import load, save
from src.evaluation import summarize

METHODS=('baseline','lexical','hybrid','mmr','rerank')

def audit_split(split, methods):
 cases=load(f'benchmark/nd13/{split}.json'); comparison={}
 for name in methods:
  folder=Path(f'results/nd13/v2/{split}/{name}')
  traces=load(folder/'traces.json'); reviews=load(folder/'reviews.json')
  labels=audit(cases,traces,reviews); save(folder/'audit_summary.json',labels)
  summary={**summarize(traces),**labels}; save(folder/'summary.json',summary)
  comparison[name]=summary
 save(f'results/nd13/v2/{split}/comparison.json',comparison)
 return comparison

def main():
 selected=load('results/nd13/v2/selection.json')['selected']
 dev=audit_split('dev',METHODS); test=audit_split('test',('baseline',selected))
 # Refresh only the derived audit summaries; frozen method, data, model, and hashes remain unchanged.
 selection=load('results/nd13/v2/selection.json'); selection['dev_comparison']=dev
 save('results/nd13/v2/selection.json',selection)
 print(f"Recomputed audit metrics. Frozen method remains {selected}; test methods: {', '.join(test)}")

if __name__=='__main__': main()
