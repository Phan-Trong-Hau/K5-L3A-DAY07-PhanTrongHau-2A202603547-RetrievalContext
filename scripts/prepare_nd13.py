"""Prepare a Day 6 style chunk/vector snapshot for the Vietnamese ND 13 external test."""
import hashlib, json, re, shutil
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fastembed import TextEmbedding
from src.common import sha256, save

DAY6 = ROOT.parent / 'K5-L3A-DAY06-PhanTrongHau-2A202603547-DataIngestion'
OUT = ROOT / 'data/nd13'
DAY6_SOURCE = DAY6 / 'data/vietnamese'
SOURCE = DAY6_SOURCE if (DAY6_SOURCE/'pages.json').exists() else OUT


def paragraph_spans(text, max_size=1000):
    spans=[]
    for match in re.finditer(r'\S[\s\S]*?(?=\n\n|$)', text):
        start,end=match.span()
        while end-start > max_size:
            cut=text.rfind(' ', start, start+max_size+1)
            cut=cut if cut>start else start+max_size
            spans.append((start,cut)); start=cut+(text[cut:cut+1]==' ')
        if start<end: spans.append((start,end))
    merged=[]
    for start,end in spans:
        if merged and end-merged[-1][0] <= max_size: merged[-1]=(merged[-1][0],end)
        else: merged.append((start,end))
    return merged


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    pages_path=SOURCE/'pages.json'
    manifest_path=(SOURCE/'manifest.json') if SOURCE==DAY6_SOURCE else (OUT/'source_manifest.json')
    pages=json.loads(pages_path.read_text())
    manifest=json.loads(manifest_path.read_text())
    pdf=SOURCE/'13nd.signed.pdf'
    if sha256(pdf)!=manifest['sha256'] or sha256(SOURCE/'pages.json')!=manifest['ocr_text_sha256']:
        raise ValueError('Day 6 Nghị định 13 source/OCR hash mismatch')
    if pdf.resolve()!=(OUT/'13nd.signed.pdf').resolve(): shutil.copy2(pdf,OUT/'13nd.signed.pdf')
    if pages_path.resolve()!=(OUT/'pages.json').resolve(): shutil.copy2(pages_path,OUT/'pages.json')
    if manifest_path.resolve()!=(OUT/'source_manifest.json').resolve(): shutil.copy2(manifest_path,OUT/'source_manifest.json')
    chunks=[]
    for page in pages:
        text=page['text']; spans=page['metadata'].get('chapter_spans') or [{'chapter':page['metadata'].get('chapter',''), 'start':0,'end':len(text)}]
        for chapter_span in spans:
            chapter=chapter_span['chapter']; a,b=chapter_span['start'],chapter_span['end']
            for start,end in paragraph_spans(text[a:b]):
                abs_start,abs_end=a+start,a+end
                body=text[abs_start:abs_end]
                cid=hashlib.sha256(f"{page['document_id']}:{page['page']}:{abs_start}:{abs_end}:{body}".encode()).hexdigest()
                chunks.append({'id':cid,'source_id':page['document_id'],'source':page['source'],'page':page['page'],'text':body,
                    'metadata':{**page['metadata'],'chapter':chapter,'start':abs_start,'end':abs_end,'document_id':page['document_id']}})
    embedder=TextEmbedding(model_name='BAAI/bge-small-en-v1.5',threads=4)
    vectors=[{'id':c['id'],'point_id':int(c['id'][:15],16),'vector':v.tolist()} for c,v in zip(chunks,embedder.passage_embed([c['text'] for c in chunks],batch_size=32))]
    save(OUT/'chunks.json',chunks); save(OUT/'vectors.json',vectors); save(OUT/'embedding.json',json.loads((ROOT/'data/day6/embedding.json').read_text()))
    files=['chunks.json','vectors.json','pages.json','source_manifest.json','embedding.json','13nd.signed.pdf']
    provenance={'source_repository':'https://github.com/Phan-Trong-Hau/K5-L3A-DAY06-PhanTrongHau-2A202603547-DataIngestion',
      'day6_collection':'Vietnamese ND 13 pages, paragraph chunks (max 1000) and BGE-small-en-v1.5 vectors',
      'source_id':'nd13','language':'vi','page_count':len(pages),'chunk_count':len(chunks),'dimensions':384,
      'embedding_model':'BAAI/bge-small-en-v1.5','source_pdf_sha256':manifest['sha256'],'sha256':{name:sha256(OUT/name) for name in files}}
    save(OUT/'provenance.json',provenance)
    questions_source=DAY6/'benchmark/vietnamese_questions.json'
    if not questions_source.exists(): questions_source=ROOT/'benchmark/nd13_questions_source.json'
    if questions_source.resolve()!=(ROOT/'benchmark/nd13_questions_source.json').resolve():
        shutil.copy2(questions_source,ROOT/'benchmark/nd13_questions_source.json')
    print(json.dumps({'pages':len(pages),'chunks':len(chunks),'vectors':len(vectors),'pdf_sha256':manifest['sha256']},ensure_ascii=False))

if __name__=='__main__': main()
