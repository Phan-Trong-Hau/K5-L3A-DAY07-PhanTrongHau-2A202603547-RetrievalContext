"""Build the presentation report from frozen ND13 v2 benchmark artifacts."""
import html
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.common import load, save

METHODS={
 'baseline':'Dense cosine', 'lexical':'BM25 tiếng Việt',
 'hybrid':'Hybrid dense + BM25 (RRF)', 'mmr':'MMR trên dense shortlist',
 'rerank':'Hybrid + MiniLM cross-encoder rerank'}

def main():
 base=Path('results/nd13/v2'); dev_cases=load('benchmark/nd13/dev.json'); test_cases=load('benchmark/nd13/test.json')
 selection=load(base/'selection.json'); unit=load('results/nd13/code_tests.json')
 dev={m:{**load(base/'dev'/m/'summary.json'),**load(base/'dev'/m/'audit_summary.json')} for m in METHODS}
 test={m:load(base/'test'/m/'summary.json') for m in ('baseline',selection['selected'])}
 traces={m:load(base/'test'/m/'traces.json') for m in test}
 reviews={m:load(base/'test'/m/'reviews.json') for m in test}
 per_case=[]
 for m,rows in traces.items():
  rmap={r['query_id']:r for r in reviews[m]}
  for q,t in zip(test_cases,rows):
   r=rmap[q['id']]
   per_case.append({'id':q['id'],'method':m,'answer_grade':r.get('answer_grade'),
    'context_grade':r.get('context_grade'),'abstention_correct':r.get('abstention_correct'),
    'status':t['status'],'hit3':t.get('hit3'),'context_hit':t.get('context_hit'),
    'answer':t.get('answer',''),'reason':r.get('reason',''),'seconds':t.get('elapsed_seconds',0)})
 validation={
  'source':'Nghị định 13/2023/NĐ-CP, Day 06 OCR snapshot','source_sha256':load('data/nd13/source_manifest.json')['sha256'],
  'ocr_sha256':load('data/nd13/source_manifest.json')['ocr_text_sha256'],
  'dev':{'cases':len(dev_cases),'answerable':sum(q['answerable'] for q in dev_cases),'unanswerable':sum(not q['answerable'] for q in dev_cases),'methods':dev},
  'test':{'cases':len(test_cases),'answerable':sum(q['answerable'] for q in test_cases),'unanswerable':sum(not q['answerable'] for q in test_cases),'selection':selection['selected'],'methods':test,'per_case':per_case},
  'unit_tests':unit,'all_end_to_end_cases_passed':False,
  'grading_note':'Frozen test results reviewed against OCR source and gold evidence. AI-assisted review; student confirmation pending. Errors count as zero for answer quality; abstention and citation support reported separately.',
  'limitations':['The 20 previously inspected Day 06 questions are dev only, not an independent holdout; preserved as external_v1 and reclassified in v2.','New v2 test contains 5 answerable and 2 evidence-absence cases; only baseline and the dev-selected BM25 method were run after selection freeze.','BGE-small-en-v1.5 and MiniLM cross-encoder retain English-labelled model names and are used with Vietnamese OCR. OCR spelling errors remain.','This is the signed 2023 text and does not establish current legal requirements or provide legal advice.']}
 save('results/nd13/validation.json',validation)
 dev_rows='\n'.join(f"| {m} | {s['selection_mean_errors_zero']:.2f}/2 | {s['false_abstention']['n']}/{s['false_abstention']['N']} | {s['context_evidence']['n']}/{s['context_evidence']['N']} | {s['abstention']['n']}/{s['abstention']['N']} | {s['errors']} | {s['median_seconds']:.1f} |" for m,s in dev.items())
 test_rows='\n'.join(f"| {m} | {s['selection_mean_errors_zero']:.2f}/2 | {s['answer_grades']['2']}/5 | {s['context_evidence']['n']}/5 | {s['abstention']['n']}/2 | {s['errors']} | {s['median_seconds']:.1f} |" for m,s in test.items())
 detail='\n'.join(f"| {html.escape(x['id'])} | {html.escape(x['method'])} | {x['status']} | {x['answer_grade'] if x['answer_grade'] is not None else '—'} | {x['context_grade'] if x['context_grade'] is not None else '—'} | {('đúng' if x['abstention_correct'] else 'sai') if x['abstention_correct'] is not None else '—'} |" for x in per_case)
 md=f'''# Demo: Agentic RAG trên Nghị định 13/2023/NĐ-CP

## Mục tiêu

So sánh năm phương pháp retrieval trên tài liệu tiếng Việt của Day 06, chọn cấu hình chỉ bằng dev, rồi đánh giá một lần trên test mới. Bản PDF ký số năm 2023 được giữ nguyên cùng OCR, chunks và vector Day 06. Không dùng bài Alice cho benchmark này.

## Thiết kế benchmark

- Dev: {len(dev_cases)} câu, 20 có đáp án và 2 câu cố ý không có bằng chứng; dùng so sánh 5 phương pháp.
- Test đóng băng: {len(test_cases)} câu mới, 5 có đáp án và 2 thiếu bằng chứng; chỉ chạy baseline và phương pháp được chọn trên dev.
- Hai mươi câu đã chạy và xem trước ở phiên trước được lưu dưới `results/nd13/external_v1/` và dùng lại làm dev; chúng không được tính là holdout độc lập.
- Quy tắc chọn: điểm answer grade trung bình trên dev (0–2; lỗi chạy tính 0), sau đó lần lượt xét abstention đúng, evidence trong context, latency.
- BM25 tiếng Việt (`lexical`) được chọn trên dev. Model: Qwen 3 4B local; corpus và code được hash/freeze trước test.

## Kết quả test mới

| Cấu hình | Answer grade TB / 2 (lỗi=0) | Đúng hoàn toàn | Gold evidence trong context | Từ chối đúng câu thiếu evidence | Lỗi | Median giây |
|---|---:|---:|---:|---:|---:|---:|
{test_rows}

BM25 trả lời đúng về nội dung ở 4/5 câu có đáp án, nhưng chỉ 3/4 citation được hỗ trợ đúng đoạn; ở `nd13-23`, câu trả lời nêu đúng điều kiện nhưng citation trỏ sang trang 15 thay vì đoạn luật ở trang 11, nên được chấm answer 1/2. BM25 từ chối đúng 2/2 câu không có bằng chứng. Câu `nd13-25` là lỗi giao thức: model lấy đúng đoạn trang 21 cho thấy kiểm tra thường niên và ngoại lệ, nhưng lại phát abstain mà không gọi retrieval theo giao thức; lượt sửa cũng bỏ retrieval nên runner ghi `error`. Điểm câu này là 0, không che lỗi bằng hit@3. Baseline trả lời đúng 1/5 câu, từ chối đúng 2/2 câu thiếu evidence, và có một lỗi giao thức.

### Chấm từng câu

| Case | Method | Trạng thái | Answer / 2 | Context / 2 | Abstention |
|---|---|---|---:|---:|---|
{detail}

## So sánh dev dùng để chọn

| Method | Answer grade TB / 2 (lỗi=0) | Từ chối nhầm / câu có đáp án | Gold evidence trong context | Từ chối đúng / câu thiếu evidence | Lỗi | Median giây |
|---|---:|---:|---:|---:|---:|---:|
{dev_rows}

## Năm phương pháp

1. Dense cosine trên vector BGE Day 06.
2. BM25 lexical trên OCR tiếng Việt.
3. Hybrid dense + BM25 bằng reciprocal-rank fusion.
4. MMR giảm các đoạn trùng lặp trong shortlist dense.
5. Rerank shortlist hybrid bằng MiniLM cross-encoder.

## Kiểm tra và giới hạn

**Unit tests: {unit['tests_run']}/{unit['tests_run']} pass.** Đây là kiểm tra code bằng mock/fake provider, không đại diện chất lượng trả lời thực tế. Test end-to-end không pass hết: BM25 có một lỗi protocol trên `nd13-25`; kết quả được giữ nguyên trong report.

Dev/test là benchmark nội bộ nhỏ, phần review ngữ nghĩa có hỗ trợ AI và cần người học xác nhận. OCR có lỗi nhận dạng. BGE-small-en-v1.5 và MiniLM là model có tên tiếng Anh được giữ từ pipeline Day 06 khi xử lý tiếng Việt. Nguồn là văn bản năm 2023, không xác nhận quy định hiện hành và không phải tư vấn pháp lý.

## Artifact để demo

- Protocol: `benchmark/nd13/protocol.json`
- Câu hỏi: `benchmark/nd13/dev.json`, `benchmark/nd13/test.json`
- Chọn cấu hình và hash: `results/nd13/v2/selection.json`
- Trace test: `results/nd13/v2/test/<method>/traces.json`
- Report dữ liệu: `results/nd13/validation.json`
- PDF nguồn: `data/nd13/13nd.signed.pdf`

Chạy lại code tests: `python3 scripts/check_tests.py`. Chạy viewer trace: `.venv/bin/python scripts/demo.py --scenario all`.
'''
 Path('report/NGHI_DINH_13_DEMO.md').write_text(md,encoding='utf-8')
 rows=''.join(f'<tr><td>{html.escape(m)}</td><td>{s["selection_mean_errors_zero"]:.2f}/2</td><td>{s["answer_grades"]["2"]}/5</td><td>{s["context_evidence"]["n"]}/5</td><td>{s["abstention"]["n"]}/2</td><td>{s["errors"]}</td><td>{s["median_seconds"]:.1f}</td></tr>' for m,s in test.items())
 case_rows=''.join(f'<tr><td>{html.escape(x["id"])}</td><td>{html.escape(x["method"])}</td><td>{x["status"]}</td><td>{x["answer_grade"] if x["answer_grade"] is not None else "—"}/2</td><td>{x["context_grade"] if x["context_grade"] is not None else "—"}/2</td><td>{("Đúng" if x["abstention_correct"] else "Sai") if x["abstention_correct"] is not None else "—"}</td></tr>' for x in per_case)
 dev_html=''.join(f'<tr><td>{html.escape(m)}</td><td>{s["selection_mean_errors_zero"]:.2f}/2</td><td>{s["context_evidence"]["n"]}/20</td><td>{s["abstention"]["n"]}/2</td><td>{s["errors"]}</td></tr>' for m,s in dev.items())
 page=f'''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Demo Nghị định 13 — Agentic RAG</title><style>
:root{{--ink:#172b3c;--muted:#5c7183;--line:#dce5ea;--blue:#185c87;--paper:#fff;--bg:#f1f5f7;--teal:#0c796c;--amber:#8a4b08}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 system-ui,-apple-system,"Segoe UI",sans-serif}}header{{padding:40px max(calc((100vw - 1050px)/2),24px);background:#10283d;color:#fff}}header span{{font-size:.8em;color:#a9cfdd;letter-spacing:.12em;text-transform:uppercase}}header h1{{font-size:clamp(2rem,5vw,3.2rem);line-height:1.12;margin:.4em 0}}header p{{max-width:780px;color:#d8e5eb}}main{{max-width:1050px;margin:26px auto;padding:0 18px}}section,article{{background:var(--paper);border:1px solid var(--line);border-radius:14px;margin:18px 0;padding:24px;box-shadow:0 5px 20px #14324a0a}}h2{{margin-top:0}}.warning{{border-left:5px solid #c87618;background:#fff9ef}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.cards div{{background:#f3f7f9;padding:14px;border-radius:10px}}.cards b,.cards span{{display:block}}.cards b{{font-size:1.35rem;color:var(--blue)}}.cards span,small,.muted{{color:var(--muted)}}table{{width:100%;border-collapse:collapse;font-size:.94rem}}th,td{{padding:10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{background:#edf4f7}}a{{color:var(--blue)}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}@media(max-width:700px){{.cards,.grid{{grid-template-columns:1fr}}table{{display:block;overflow-x:auto;white-space:nowrap}}main{{padding:0 12px}}section,article{{padding:17px}}}}@media print{{body{{background:white}}header{{padding:24px}}main{{margin:auto}}section,article{{break-inside:avoid;box-shadow:none}}}}
</style><header><span>Day 07 · Agentic RAG · Benchmark tiếng Việt</span><h1>Hỏi đáp trên Nghị định 13</h1><p>So sánh 5 phương pháp trên OCR Day 06, chọn bằng dev và đánh giá trên 7 câu test mới có kiểm soát thiếu bằng chứng.</p></header><main>
<article class="warning"><h2>Kết quả cần trình bày trung thực</h2><p><b>BM25 là phương pháp được chọn từ dev.</b> Trên test mới, câu trả lời đúng về nội dung ở 4/5 câu có đáp án; citation được hỗ trợ đúng đoạn ở 3/4 câu trả lời có citation; abstain đúng 2/2 câu thiếu evidence. Citation của `nd13-23` trỏ nhầm sang trang 15 nên answer grade là 1/2. Một case bị lỗi protocol dù retrieval tìm thấy đoạn luật. {unit['tests_run']}/{unit['tests_run']} unit tests pass; điều đó không đồng nghĩa mọi câu hỏi end-to-end pass.</p><p>BM25 tìm thấy đoạn trang 21 cho `nd13-25`, nhưng model không thực hiện retrieval theo protocol và sau bước repair vẫn abstain. Kết quả case được chấm 0 và không được tính là end-to-end pass.</p></article>
<section><h2>Test mới sau khi freeze lựa chọn</h2><div class="grid"><div><p><b>BM25 · {test[selection['selected']]['selection_mean_errors_zero']:.2f}/2</b><br>Đúng hoàn toàn: {test[selection['selected']]['answer_grades']['2']}/5 câu có đáp án<br>Context có evidence: {test[selection['selected']]['context_evidence']['n']}/5<br>Abstain đúng: {test[selection['selected']]['abstention']['n']}/2<br>Lỗi: {test[selection['selected']]['errors']}</p></div><div><p><b>Baseline · {test['baseline']['selection_mean_errors_zero']:.2f}/2</b><br>Đúng hoàn toàn: {test['baseline']['answer_grades']['2']}/5 câu có đáp án<br>Context có evidence: {test['baseline']['context_evidence']['n']}/5<br>Abstain đúng: {test['baseline']['abstention']['n']}/2<br>Lỗi: {test['baseline']['errors']}</p></div></div><table><thead><tr><th>Method</th><th>Answer TB / 2 (lỗi=0)</th><th>Đúng hoàn toàn</th><th>Evidence context</th><th>Abstain đúng</th><th>Lỗi</th><th>Median giây</th></tr></thead><tbody>{rows}</tbody></table><h3>Đối chiếu từng case</h3><table><thead><tr><th>Case</th><th>Method</th><th>Trạng thái</th><th>Answer</th><th>Context</th><th>Abstain</th></tr></thead><tbody>{case_rows}</tbody></table></section>
<section><h2>Dev và cách chọn</h2><p>Dev gồm 20 câu trả lời được, 2 câu thiếu bằng chứng; 5 phương pháp được đo trước khi khóa cấu hình. Chọn theo answer grade trung bình (0–2, lỗi tính 0), rồi abstention, evidence trong context, latency. BM25 lexical được chọn.</p><table><thead><tr><th>Method</th><th>Answer TB / 2 (lỗi=0)</th><th>Evidence context</th><th>Abstain đúng</th><th>Lỗi</th></tr></thead><tbody>{dev_html}</tbody></table><p class="muted">Hai mươi trace đã xem trước được phân loại lại thành dev, lưu riêng ở external_v1; không xem chúng là test độc lập. Test v2 được tạo và đóng băng trước khi chạy.</p></section>
<section><h2>Năm phương pháp</h2><ol><li>Dense cosine với vector BGE Day 06.</li><li>BM25 lexical cho OCR tiếng Việt.</li><li>Hybrid dense + BM25 bằng reciprocal-rank fusion.</li><li>MMR giảm trùng lặp trong shortlist.</li><li>Hybrid shortlist rồi rerank bằng MiniLM cross-encoder.</li></ol></section>
<section><h2>Nguồn, giới hạn và file demo</h2><p><a href="../data/nd13/13nd.signed.pdf">PDF Nghị định 13</a> · <a href="../benchmark/nd13/protocol.json">Protocol</a> · <a href="NGHI_DINH_13_DEMO.md">Báo cáo Markdown</a> · <a href="../results/nd13/validation.json">Metrics JSON</a> · <a href="../results/nd13/v2/selection.json">Lựa chọn đã freeze</a>.</p><p>Nguồn là bản ký số năm 2023. OCR còn lỗi nhận dạng. BGE-small-en-v1.5 và MiniLM được giữ từ pipeline Day 06 khi truy xuất tiếng Việt. Review ngữ nghĩa được AI hỗ trợ và cần người học xác nhận. Báo cáo không xác nhận quy định hiện hành và không phải tư vấn pháp lý.</p></section><footer class="muted">Nguồn: Day 06 · Unit tests: {unit['tests_run']}/{unit['tests_run']} pass · Test end-to-end có một lỗi BM25.</footer></main></html>'''
 Path('report/NGHI_DINH_13_DEMO.html').write_text(page,encoding='utf-8')
 print(f"Wrote report/NGHI_DINH_13_DEMO.html and .md; selected={selection['selected']}; tests={unit['tests_run']}")

if __name__=='__main__': main()
