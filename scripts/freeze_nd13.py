"""Audit dev labels and freeze config/model/core before the fresh ND13 test."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from scripts.freeze import audit
from src.common import load, save, sha256, utc
from src.evaluation import summarize

METHODS=('baseline','lexical','hybrid','mmr','rerank')

def main():
 root=Path('results/nd13/v2')
 if (root/'selection.json').exists(): raise ValueError('Selection already frozen')
 cases=load('benchmark/nd13/dev.json'); comparison={}
 for name in METHODS:
  folder=root/'dev'/name
  traces=load(folder/'traces.json'); reviews=load(folder/'reviews.json')
  audited=audit(cases,traces,reviews)
  save(folder/'audit_summary.json',audited)
  comparison[name]={**summarize(traces),**audited}
 if set(comparison)!=set(METHODS): raise ValueError('All methods must finish dev')
 manifests=[load(root/'dev'/name/'manifest.json') for name in METHODS]
 if len({m['model_digest'] for m in manifests})!=1: raise ValueError('Dev model digest mismatch')
 if any(m['code_sha256']!=manifests[0]['code_sha256'] for m in manifests): raise ValueError('Core code differs across dev methods')
 for path,digest in manifests[0]['code_sha256'].items():
  if sha256(path)!=digest: raise ValueError(f'Core code changed after dev: {path}')
 winner=min(METHODS,key=lambda name:(-comparison[name]['selection_mean_errors_zero'],
  -(comparison[name]['abstention']['rate'] or 0),-(comparison[name]['context_evidence']['rate'] or 0),
  comparison[name]['median_seconds'],name))
 selection={'selected':winner,'frozen_at':utc(),
  'criterion':'Highest dev mean answer_grade (errors count as zero); ties: correct abstention rate, context evidence rate, median latency, method name.',
  'dev_sha256':sha256('benchmark/nd13/dev.json'),'test_sha256':sha256('benchmark/nd13/test.json'),
  'config_sha256':sha256('configs/experiments.json'),'corpus_sha256':sha256('data/nd13/provenance.json'),
  'code_sha256':manifests[0]['code_sha256'],'model_digest':manifests[0]['model_digest'],
  'review_sha256':{name:sha256(root/'dev'/name/'reviews.json') for name in METHODS},
  'trace_reclassification':'20 already-inspected Day 06 external cases reused as dev; imported trace_origin is preserved. New test set is separate and has not been run.',
  'dev_comparison':comparison}
 save(root/'comparison.json',comparison); save(root/'selection.json',selection)
 print(json.dumps({'selected':winner,'dev_comparison':{m:{k:comparison[m][k] for k in ['selection_mean_errors_zero','grounded_mean','abstention','false_abstention','context_evidence','hit3','errors','median_seconds']} for m in METHODS}},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
