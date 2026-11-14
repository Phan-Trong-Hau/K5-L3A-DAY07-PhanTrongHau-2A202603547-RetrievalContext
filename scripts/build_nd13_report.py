"""Build the current Vietnamese Nghị định 13 result summary and offline HTML demo."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.common import load, save, sha256

METHODS={
 'baseline':'Dense cosine (Day 6 BGE vectors, top-3)',
 'lexical':'BM25 tiếng Việt (token từ OCR)',
 'hybrid':'Hybrid dense + BM25, reciprocal-rank fusion',
 'mmr':'MMR trên dense top-20, λ = 0,75',
 'rerank':'Hybrid top-20, MiniLM cross-encoder rerank',
}

def main():
    cases=load('benchmark/nd13/test.json'); unit=load('results/nd13/code_tests.json')
    stats={}; all_cases=[]
    for key,label in METHODS.items():
        traces=load(f'results/nd13/test/{key}/traces.json')
        assert len(traces)==len(cases)==20
        errors=sum(t['status']=='error' for t in traces)
        answered=sum(t['status']=='answered' for t in traces)
        context=sum(bool(t.get('context_hit')) for t in traces)
        hit3=sum(bool(t.get('hit3')) for t in traces)
        searched=sum(any(e.get('event')=='search' for e in t.get('events',[])) for t in traces)
        citation_inside=sum(bool(t.get('citations')) and set(t['citations'])<=set(t.get('context_ids',[])) for t in traces)
        stats[key]={'label':label,'N':len(traces),'answered':answered,'errors':errors,'abstained':len(traces)-answered-errors,
                    'hit3':hit3,'context_evidence':context,'searched':searched,'citations_in_context':citation_inside,
                    'median_seconds':sorted(t.get('elapsed_seconds',0) for t in traces)[len(traces)//2]}
        for q,t in zip(cases,traces):
            all_cases.append({'id':q['id'],'question':q['question'],'method':key,'status':t['status'],
                'hit3':bool(t.get('hit3')),'context_evidence':bool(t.get('context_hit')),'answer':t.get('answer','')[:500]})
    validation={'source':'Nghị định 13/2023/NĐ-CP (Day 06 Vietnamese OCR snapshot)',
      'source_sha256':load('data/nd13/source_manifest.json')['sha256'],
      'ocr_sha256':load('data/nd13/source_manifest.json')['ocr_text_sha256'],
      'test_cases':len(cases),'methods':stats,'unit_tests':unit,
      'all_end_to_end_cases_passed':False,
      'grading_note':'No automatic semantic grade is assigned. A correct endpoint answer needs semantic correctness, support from cited passage, and citation membership in the final context. Answered status and retrieval hits are reported separately.',
      'limitations':['All 20 cases are the frozen Day 06 external test; there is no ND13 dev set and no winner is selected from these test results.',
        'BGE-small-en-v1.5 and the MiniLM cross-encoder are English-labelled models applied to Vietnamese OCR; BM25 tokenization does not normalize OCR spelling.',
        'The document is the signed 2023 snapshot; this benchmark is not legal advice and makes no claim about current law.']}
    save('results/nd13/validation.json',validation)
    rows=[]
    for key,s in stats.items():
        rows.append(f"| {key} | {s['answered']}/20 | {s['errors']} | {s['hit3']}/20 | {s['context_evidence']}/20 | {s['searched']}/20 | {s['citations_in_context']}/20 |")
    table='\n'.join(rows)
    report=f'''# Agentic RAG trên Nghị định 13/2023/NĐ-CP

**Bộ dữ liệu đánh giá hiện tại:** tài liệu tiếng Việt từ Day 06, OCR 39 trang; 88 đoạn, vector BGE-small-en-v1.5 384 chiều; 20 câu hỏi đóng băng trước khi chạy. Nguồn là [bản ký số năm 2023 do Chính phủ công bố](https://chinhphu.vn/default.aspx?docid=207759&pageid=27160). Bài Alice không được dùng cho kết quả trong báo cáo này.

## Kết quả kiểm tra

| Phương pháp | Agent trả lời | Lỗi chạy | Gold trong top-3 truy vấn gốc | Gold trong context cuối | Đã gọi search | Citation nằm trong context |
|---|---:|---:|---:|---:|---:|---:|
{table}

**Unit tests: {unit['tests_run']}/{unit['tests_run']} pass.** Đây là kiểm tra code với mock/fake provider; không xác nhận chất lượng ngữ nghĩa của model.

Không phải mọi case end-to-end đều đạt. Bằng chứng retrieval, trạng thái `answered`, và tính đúng đắn của câu trả lời được đo riêng. Ví dụ reranker trả lời sai câu `vi03` (nhầm “Bên Kiểm soát dữ liệu cá nhân” thành “Bên Kiểm soát và xử lý dữ liệu cá nhân”); BM25 trả lời `ABSTAIN` cho `vi04` dù đoạn luật có trong context; một số câu bị bỏ sót bởi dense/MMR. Không gọi trạng thái answered là pass nếu chưa kiểm tra đáp án và citation về mặt nghĩa.

## Năm phương pháp

1. **Dense:** cosine trên vector BGE Day 06.
2. **BM25:** lexical matching trên OCR tiếng Việt.
3. **Hybrid:** reciprocal-rank fusion của dense và BM25.
4. **MMR:** chọn đoạn liên quan nhưng giảm trùng lặp trong shortlist dense.
5. **Rerank:** hybrid shortlist, chấm cặp query–document bằng MiniLM cross-encoder.

Cả 20 câu external test đã được chạy qua cả năm phương pháp (100 lượt). Chúng tôi không chọn winner hoặc chỉnh tham số bằng chính tập test này. Không có ND13 dev set trong lần đánh giá này.

## Giới hạn

Embedding và cross-encoder được giữ nguyên từ pipeline Day 06, cả hai có tên model tiếng Anh và được áp dụng lên tiếng Việt; vì thế kết quả không đại diện cho chất lượng tối đa của mô hình đa ngữ. OCR giữ nguyên các lỗi nhận dạng trong nguồn. Nghị định là bản ký số năm 2023, không phải tư vấn pháp lý hay xác nhận quy định hiện hành.

## Tái lập

```bash
.venv/bin/python scripts/prepare_nd13.py
.venv/bin/python scripts/run_nd13.py
python3 scripts/check_tests.py
.venv/bin/python scripts/build_nd13_report.py
```

Protocol đóng băng: `benchmark/nd13/protocol.json`. Chi tiết trace từng phương pháp: `results/nd13/test/<method>/traces.json`. PDF và OCR snapshot được giữ tại `data/nd13/`.
'''
    Path('report/NGHI_DINH_13_DEMO.md').write_text(report,encoding='utf-8')
    import html
    body=''.join(f'<tr><td>{html.escape(k)}</td><td>{s["answered"]}/20</td><td>{s["errors"]}</td><td>{s["hit3"]}/20</td><td>{s["context_evidence"]}/20</td><td>{s["searched"]}/20</td><td>{s["citations_in_context"]}/20</td></tr>' for k,s in stats.items())
    test_cards=''.join(f'<section class="method"><h3>{html.escape(k)} <small>{s["label"]}</small></h3><div class="cards"><div><b>{s["answered"]}/20</b><span>agent answered</span></div><div><b>{s["context_evidence"]}/20</b><span>gold in context</span></div><div><b>{s["hit3"]}/20</b><span>gold in original top-3</span></div><div><b>{s["errors"]}</b><span>runtime errors</span></div></div></section>' for k,s in stats.items())
    page=f'''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Demo Nghị định 13 — Agentic RAG</title><style>
:root{{--ink:#172b3c;--muted:#5c7183;--line:#dce5ea;--blue:#185c87;--paper:#fff;--bg:#f1f5f7;--teal:#0c796c}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 system-ui,-apple-system,"Segoe UI",sans-serif}}header{{padding:36px max(calc((100vw - 1040px)/2),24px);background:#10283d;color:white}}header span{{font-size:.8em;color:#a9cfdd;letter-spacing:.12em;text-transform:uppercase}}header h1{{font-size:clamp(2rem,5vw,3.3rem);line-height:1.12;margin:.4em 0}}header p{{max-width:780px;color:#d8e5eb}}main{{max-width:1040px;margin:28px auto;padding:0 20px}}section,article{{background:var(--paper);border:1px solid var(--line);border-radius:14px;margin:18px 0;padding:24px;box-shadow:0 5px 20px #14324a0a}}h2{{margin-top:0}}.warning{{border-left:5px solid #c87618;background:#fff9ef}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.cards div{{background:#f3f7f9;padding:14px;border-radius:10px}}.cards b,.cards span{{display:block}}.cards b{{font-size:1.35rem;color:var(--blue)}}.cards span,small{{color:var(--muted)}}table{{width:100%;border-collapse:collapse;font-size:.94rem}}th,td{{padding:10px;border-bottom:1px solid var(--line);text-align:left}}th{{background:#edf4f7}}code,pre{{background:#edf4f7;border-radius:5px;padding:2px 5px;overflow:auto}}.method h3{{margin-top:0}}a{{color:var(--blue)}}.small{{font-size:.93rem;color:var(--muted)}}@media(max-width:700px){{.cards{{grid-template-columns:repeat(2,1fr)}}table{{display:block;overflow-x:auto;white-space:nowrap}}main{{padding:0 12px}}section,article{{padding:17px}}}}@media print{{body{{background:white}}header{{padding:24px;color:white}}main{{margin:0 auto}}section,article{{break-inside:avoid;box-shadow:none}}}}
</style><header><span>Day 07 · Agentic RAG · Vietnamese external test</span><h1>Hỏi đáp trên Nghị định 13</h1><p>So sánh 5 phương pháp retrieval trên tài liệu tiếng Việt đã OCR từ bộ Day 06. 20 câu × 5 phương pháp. Trace lưu theo từng case.</p></header><main>
<article class="warning"><h2>Kiểm tra đã xong — không phải mọi case đều đạt</h2><p><strong>{unit['tests_run']}/{unit['tests_run']} unit tests pass.</strong> Đây là test code bằng mock; chất lượng model trên từng câu cần được đánh giá riêng. Các số dưới đây tách trạng thái trả lời khỏi bằng chứng truy xuất.</p><p>Ví dụ: reranker trả lời sai vi03; BM25 từ chối vi04 dù evidence nằm trong context. Do đó không thể nói toàn bộ end-to-end cases đều pass.</p></article>
<section><h2>Tổng hợp kết quả</h2><table><thead><tr><th>Method</th><th>Answered</th><th>Lỗi</th><th>Gold top-3</th><th>Gold context</th><th>Search</th><th>Citation trong context</th></tr></thead><tbody>{body}</tbody></table><p class="small">“Gold context” không chứng minh câu trả lời đúng hoặc citation có hỗ trợ đúng nhận định; mỗi câu vẫn cần semantic review.</p></section>
{test_cards}
<section><h2>Các phương pháp</h2><ol><li>Dense cosine với vector Day 06.</li><li>BM25 lexical cho OCR tiếng Việt.</li><li>Hybrid dense + BM25, reciprocal-rank fusion.</li><li>MMR: tối ưu liên quan và giảm trùng lặp.</li><li>Rerank: hybrid shortlist + MiniLM cross-encoder.</li></ol><p>Cùng một bộ test, cùng model Qwen 3 4B local, cùng agent tiếng Việt. Không chọn phương pháp hay điều chỉnh tham số theo chính 20 câu này.</p></section>
<section><h2>Nguồn và giới hạn</h2><p><a href="../data/nd13/13nd.signed.pdf">Mở PDF ký số Nghị định 13/2023</a> · <a href="../benchmark/nd13/protocol.json">Protocol</a> · <a href="NGHI_DINH_13_DEMO.md">Báo cáo Markdown</a> · <a href="../results/nd13/validation.json">Kết quả JSON</a>.</p><p>Nguồn là bản ký số năm 2023; báo cáo không xác nhận quy định hiện hành và không phải tư vấn pháp lý. OCR giữ các lỗi nhận dạng. BGE-small-en-v1.5 và MiniLM là model gốc tiếng Anh, được giữ từ Day06 khi truy xuất tiếng Việt; đây là giới hạn domain.</p></section>
<section><h2>Chạy lại</h2><pre>.venv/bin/python scripts/prepare_nd13.py
.venv/bin/python scripts/run_nd13.py
python3 scripts/check_tests.py</pre></section></main></html>'''
    Path('report/NGHI_DINH_13_DEMO.html').write_text(page,encoding='utf-8')
    print(json.dumps({'unit_tests':unit,'methods':{k:{x:s[x] for x in ('answered','errors','hit3','context_evidence','searched')} for k,s in stats.items()},'html':'report/NGHI_DINH_13_DEMO.html'},ensure_ascii=False))

if __name__=='__main__': main()
