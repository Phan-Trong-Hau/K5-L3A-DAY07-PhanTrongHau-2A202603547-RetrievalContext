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

def pct(metric):
 return f"{metric['n']}/{metric['N']} ({metric['rate']:.0%})" if metric['N'] else '0/0 (N/A)'

def search_dist(summary):
 return ', '.join(f"{count} câu: {n} lượt" for n,count in summary['search_count_distribution'].items())

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
    'answer':t.get('answer') or t.get('error',''),'reason':r.get('reason',''),'seconds':t.get('elapsed_seconds',0)})
 validation={
  'source':'Nghị định 13/2023/NĐ-CP, Day 06 OCR snapshot','source_sha256':load('data/nd13/source_manifest.json')['sha256'],
  'ocr_sha256':load('data/nd13/source_manifest.json')['ocr_text_sha256'],
  'dev':{'cases':len(dev_cases),'answerable':sum(q['answerable'] for q in dev_cases),'unanswerable':sum(not q['answerable'] for q in dev_cases),'methods':dev},
  'test':{'cases':len(test_cases),'answerable':sum(q['answerable'] for q in test_cases),'unanswerable':sum(not q['answerable'] for q in test_cases),'selection':selection['selected'],'methods':test,'per_case':per_case},
  'unit_tests':unit,'all_end_to_end_cases_passed':False,
  'grading_note':'Frozen test results reviewed against OCR source and gold evidence. AI-assisted review; student confirmation pending. Errors count as zero for answer quality and remain in the denominator; context grade uses the actual final context. Abstention and citation support are reported separately.',
  'limitations':['The 20 previously inspected Day 06 questions are dev only, not an independent holdout; preserved as external_v1 and reclassified in v2.','New v2 test contains 5 answerable and 2 evidence-absence cases; only baseline and the dev-selected BM25 method were run after selection freeze.','BGE-small-en-v1.5 and MiniLM cross-encoder retain English-labelled model names and are used with Vietnamese OCR. OCR spelling errors remain.','This is the signed 2023 text and does not establish current legal requirements or provide legal advice.']}
 save('results/nd13/validation.json',validation)
 dev_rows='\n'.join(f"| {m} | {pct(s['hit1'])} | {pct(s['hit3'])} | {pct(s['context_evidence'])} | {s['answer_grades']['0']}/{s['answer_grades']['1']}/{s['answer_grades']['2']} ({s['grounded_mean']:.2f}/2) | {s['context_grades']['0']}/{s['context_grades']['1']}/{s['context_grades']['2']} | {pct(s['citation_support'])} | {pct(s['citation_coverage'])} | {pct(s['tool_use'])} | {search_dist(s)} | {pct(s['abstention'])} | {pct(s['false_abstention'])} | {s['errors']} | {s['median_seconds']:.1f} | {s['total_seconds']:.1f} | {s['prompt_tokens']+s['completion_tokens']} | ${s['service_cost_usd']:.2f} |" for m,s in dev.items())
 test_rows='\n'.join(f"| {m} | {pct(s['hit1'])} | {pct(s['hit3'])} | {pct(s['context_evidence'])} | {s['answer_grades']['0']}/{s['answer_grades']['1']}/{s['answer_grades']['2']} ({s['grounded_mean']:.2f}/2) | {s['context_grades']['0']}/{s['context_grades']['1']}/{s['context_grades']['2']} | {pct(s['citation_support'])} | {pct(s['citation_coverage'])} | {pct(s['tool_use'])} | {search_dist(s)} | {pct(s['abstention'])} | {pct(s['false_abstention'])} | {s['errors']} | {s['median_seconds']:.1f} | {s['total_seconds']:.1f} | {s['prompt_tokens']+s['completion_tokens']} | ${s['service_cost_usd']:.2f} |" for m,s in test.items())
 config_rows=[]
 for m in METHODS:
  c=load(base/'dev'/m/'manifest.json')['config']
  config_rows.append(f"| {m} | {c['method']} | {c['top_k']} | {c.get('candidates','—')} | {c['budget']} ký tự | {c['max_searches']} | {c['hypothesis']} |")
 configs_md='\n'.join(config_rows)
 config_html=''.join(f'<tr><td>{html.escape(m)}</td><td>{c["method"]}</td><td>{c["top_k"]}</td><td>{c.get("candidates","—")}</td><td>{c["budget"]}</td><td>{c["max_searches"]}</td><td>{html.escape(c["hypothesis"])}</td></tr>' for m in METHODS for c in [load(base/'dev'/m/'manifest.json')['config']])
 detail='\n'.join(f"| {html.escape(x['id'])} | {html.escape(x['method'])} | {x['status']} | {x['answer_grade'] if x['answer_grade'] is not None else '—'} | {x['context_grade'] if x['context_grade'] is not None else '—'} | {('đúng' if x['abstention_correct'] else 'sai') if x['abstention_correct'] is not None else '—'} | {html.escape(x['answer'][:260]).replace('|','\\|')} | {html.escape(x['reason'])} |" for x in per_case)
 md=f'''# Demo: Agentic RAG trên Nghị định 13/2023/NĐ-CP

## Mục tiêu

So sánh năm phương pháp retrieval trên tài liệu tiếng Việt của Day 06, chọn cấu hình chỉ bằng dev, rồi đánh giá một lần trên test mới. Bản PDF ký số năm 2023 được giữ nguyên cùng OCR, chunks và vector Day 06. Không dùng bài Alice cho benchmark này.

## Thiết kế benchmark

- Dev: {len(dev_cases)} câu, 20 có đáp án và 2 câu cố ý không có bằng chứng; dùng so sánh 5 phương pháp.
- Test đóng băng: {len(test_cases)} câu mới, 5 có đáp án và 2 thiếu bằng chứng; chỉ chạy baseline và phương pháp được chọn trên dev.
- Hai mươi câu đã chạy và xem trước ở phiên trước được lưu dưới `results/nd13/external_v1/` và dùng lại làm dev; chúng không được tính là holdout độc lập.
- Quy tắc chọn: điểm answer grade trung bình trên dev (0–2; lỗi chạy tính 0), sau đó lần lượt xét abstention đúng, evidence trong context, latency.
- BM25 tiếng Việt (`lexical`) được chọn trên dev. Model: Qwen 3 4B local; corpus và code được hash/freeze trước test.

## Cấu hình và giả thuyết đã đo

| Cấu hình | Retrieval | top-k | candidates | Context budget | Tìm tối đa | Giả thuyết |
|---|---|---:|---:|---:|---:|---|
{configs_md}

BM25 thử khớp từ vựng chính xác với context lớn hơn, kỳ vọng giữ tên/điều kiện OCR bị dense bỏ sót. Hybrid thử hợp nhất thứ hạng dense và BM25 bằng RRF, kỳ vọng lấy được evidence bị một nhánh bỏ qua. Đây là so sánh giữa các cấu hình gói, chưa tách ablation tác động riêng của context budget.

## Kết quả test mới

| Cấu hình | Hit@1 | Evidence Hit@3 | Context evidence | Answer 0/1/2, TB /2 | Context 0/1/2 | Citation hỗ trợ | Trả lời có citation | Tool use* | Phân bố lượt search | Abstain đúng | Từ chối nhầm | Lỗi | Median s | Tổng s | Token tổng | Phí dịch vụ |
|---|---:|---:|---:|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
{test_rows}

BM25 trả lời đúng về nội dung ở 4/5 câu có đáp án, nhưng chỉ 3/4 citation được hỗ trợ đúng đoạn; ở `nd13-23`, câu trả lời nêu đúng điều kiện nhưng citation trỏ sang trang 15 thay vì đoạn luật ở trang 11, nên được chấm answer 1/2. BM25 từ chối đúng 2/2 câu không có bằng chứng. Câu `nd13-25` là lỗi giao thức: model bỏ qua retrieval bắt buộc và kết thúc bằng lỗi. Ranking truy vấn gốc được tính độc lập sau lượt chạy có đoạn bằng chứng trang 21, nhưng đoạn đó không nằm trong context cuối gửi model; không tính ranking offline thành retrieval thành công của agent. Điểm câu này là 0. Baseline trả lời đúng 1/5 câu, từ chối đúng 2/2 câu thiếu evidence, và có một lỗi giao thức.

### Chấm từng câu

| Case | Method | Trạng thái | Answer / 2 | Context / 2 | Abstention | Câu trả lời / lỗi | Nhận xét đối chiếu |
|---|---|---|---:|---:|---|---|---|
{detail}

## So sánh dev dùng để chọn

| Method | Hit@1 | Evidence Hit@3 | Context evidence | Answer 0/1/2, TB /2 | Context 0/1/2 | Citation hỗ trợ | Trả lời có citation | Tool use* | Phân bố lượt search | Abstain đúng | Từ chối nhầm | Lỗi | Median s | Tổng s | Token tổng | Phí dịch vụ |
|---|---:|---:|---:|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
{dev_rows}

## Hai lỗi dev đã đối chiếu

- `vi03` (định nghĩa Bên Kiểm soát): dense, hybrid, MMR và rerank đều trả lời nhầm vai trò “Bên Kiểm soát và xử lý dữ liệu cá nhân”; BM25 tìm thấy gold trong top-3/context nhưng lỗi citation-format repair. Đoạn luật ở trang 3 phân biệt hai thuật ngữ sát nhau. Đây là lỗi hiểu/giữ tên pháp lý và format citation; thêm retriever không tự giải quyết, cần output validation và đọc sát định nghĩa.
- `vi08` (rút lại đồng ý): BM25 tìm đủ evidence nhưng lỗi `Invalid citations after format repair`; hybrid và rerank trên cùng dev trả lời grade 2 với citation được hỗ trợ, còn baseline từ chối do không đưa evidence vào context. So sánh trace cho thấy retrieval đủ không bảo đảm agent kết thúc hợp lệ; lựa chọn BM25 vẫn dựa trên điểm trung bình toàn dev, không sửa theo test.

Đây là phân tích chéo các phương pháp trên cùng dev, không phải ablation sau khi sửa lỗi. Không dùng test để điều chỉnh.

* Tool use dùng mẫu số các case hoàn thành; lỗi được báo riêng. False abstention và answer grade tính trên toàn bộ câu có đáp án; runtime error được chấm 0. Citation support yêu cầu ID nằm trong context và nội dung citation hỗ trợ claim. Latency gồm toàn bộ agent run, token là tổng prompt + completion, phí dịch vụ local bằng 0 USD (điện/phần cứng chưa tính).

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
 rows=''.join(f'<tr><td>{html.escape(m)}</td><td>{pct(s["hit1"])}</td><td>{pct(s["hit3"])}</td><td>{pct(s["context_evidence"])}</td><td>{s["answer_grades"]["0"]}/{s["answer_grades"]["1"]}/{s["answer_grades"]["2"]}; {s["grounded_mean"]:.2f}/2</td><td>{s["context_grades"]["0"]}/{s["context_grades"]["1"]}/{s["context_grades"]["2"]}</td><td>{pct(s["citation_support"])}</td><td>{pct(s["citation_coverage"])}</td><td>{pct(s["tool_use"])}</td><td>{search_dist(s)}</td><td>{pct(s["abstention"])}</td><td>{pct(s["false_abstention"])}</td><td>{s["errors"]}</td><td>{s["median_seconds"]:.1f}</td><td>{s["total_seconds"]:.1f}</td><td>{s["prompt_tokens"]+s["completion_tokens"]}</td><td>${s["service_cost_usd"]:.2f}</td></tr>' for m,s in test.items())
 case_rows=''.join(f'<tr><td>{html.escape(x["id"])}</td><td>{html.escape(x["method"])}</td><td>{x["status"]}</td><td>{x["answer_grade"] if x["answer_grade"] is not None else "—"}/2</td><td>{x["context_grade"] if x["context_grade"] is not None else "—"}/2</td><td>{("Đúng" if x["abstention_correct"] else "Sai") if x["abstention_correct"] is not None else "—"}</td><td>{html.escape(x["answer"][:260])}</td><td>{html.escape(x["reason"])}</td></tr>' for x in per_case)
 dev_html=''.join(f'<tr><td>{html.escape(m)}</td><td>{pct(s["hit1"])}</td><td>{pct(s["hit3"])}</td><td>{pct(s["context_evidence"])}</td><td>{s["answer_grades"]["0"]}/{s["answer_grades"]["1"]}/{s["answer_grades"]["2"]}; {s["grounded_mean"]:.2f}/2</td><td>{s["context_grades"]["0"]}/{s["context_grades"]["1"]}/{s["context_grades"]["2"]}</td><td>{pct(s["citation_support"])}</td><td>{pct(s["citation_coverage"])}</td><td>{pct(s["tool_use"])}</td><td>{search_dist(s)}</td><td>{pct(s["abstention"])}</td><td>{pct(s["false_abstention"])}</td><td>{s["errors"]}</td><td>{s["median_seconds"]:.1f}</td><td>{s["total_seconds"]:.1f}</td><td>{s["prompt_tokens"]+s["completion_tokens"]}</td><td>${s["service_cost_usd"]:.2f}</td></tr>' for m,s in dev.items())
 page=f'''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Demo Nghị định 13 — Agentic RAG</title><style>
:root{{--ink:#172b3c;--muted:#5c7183;--line:#dce5ea;--blue:#185c87;--paper:#fff;--bg:#f1f5f7;--teal:#0c796c;--amber:#8a4b08}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 system-ui,-apple-system,"Segoe UI",sans-serif}}header{{padding:40px max(calc((100vw - 1050px)/2),24px);background:#10283d;color:#fff}}header span{{font-size:.8em;color:#a9cfdd;letter-spacing:.12em;text-transform:uppercase}}header h1{{font-size:clamp(2rem,5vw,3.2rem);line-height:1.12;margin:.4em 0}}header p{{max-width:780px;color:#d8e5eb}}main{{max-width:1050px;margin:26px auto;padding:0 18px}}section,article{{background:var(--paper);border:1px solid var(--line);border-radius:14px;margin:18px 0;padding:24px;box-shadow:0 5px 20px #14324a0a}}h2{{margin-top:0}}.warning{{border-left:5px solid #c87618;background:#fff9ef}}.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}.cards div{{background:#f3f7f9;padding:14px;border-radius:10px}}.cards b,.cards span{{display:block}}.cards b{{font-size:1.35rem;color:var(--blue)}}.cards span,small,.muted{{color:var(--muted)}}table{{width:100%;border-collapse:collapse;font-size:.94rem}}th,td{{padding:10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{background:#edf4f7}}a{{color:var(--blue)}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}@media(max-width:700px){{.cards,.grid{{grid-template-columns:1fr}}table{{display:block;overflow-x:auto;white-space:nowrap}}main{{padding:0 12px}}section,article{{padding:17px}}}}@media print{{body{{background:white}}header{{padding:24px}}main{{margin:auto}}section,article{{break-inside:avoid;box-shadow:none}}}}
</style><header><span>Day 07 · Agentic RAG · Benchmark tiếng Việt</span><h1>Hỏi đáp trên Nghị định 13</h1><p>So sánh 5 phương pháp trên OCR Day 06, chọn bằng dev và đánh giá trên 7 câu test mới có kiểm soát thiếu bằng chứng.</p></header><main>
<article class="warning"><h2>Kết quả cần trình bày trung thực</h2><p><b>BM25 là phương pháp được chọn từ dev.</b> Trên test mới, câu trả lời đúng về nội dung ở 4/5 câu có đáp án; citation được hỗ trợ đúng đoạn ở 3/4 câu trả lời có citation; abstain đúng 2/2 câu thiếu evidence. Citation của `nd13-23` trỏ nhầm sang trang 15 nên answer grade là 1/2. Một case bị lỗi protocol. {unit['tests_run']}/{unit['tests_run']} unit tests pass; điều đó không đồng nghĩa mọi câu hỏi end-to-end pass.</p><p>Ở `nd13-25`, model không gọi retrieval bắt buộc và sau bước repair kết thúc bằng lỗi. Ranking query gốc được đo độc lập ngoài lượt agent có hit trang 21, nhưng trang này không vào context model. Không tính đây là retrieval thành công.</p></article>
<section><h2>Test mới sau khi freeze lựa chọn</h2><p>BM25 được chọn trên dev; bảng dùng mẫu số toàn bộ câu có đáp án, và runtime error nhận answer grade 0; context grade phản ánh context thật trong trace. *Tool use dùng mẫu số case chạy thành công; lỗi được báo riêng. Citation hỗ trợ đòi hỏi ID trong context và đoạn được dẫn hỗ trợ claim.</p><div style="overflow-x:auto"><table><thead><tr><th>Method</th><th>Hit@1</th><th>Hit@3</th><th>Context</th><th>Answer 0/1/2; mean</th><th>Context 0/1/2</th><th>Citation support</th><th>Answered w/citation</th><th>Tool use*</th><th>Search count distribution</th><th>Abstain</th><th>False abstain</th><th>Errors</th><th>Median s</th><th>Total s</th><th>Tokens</th><th>Cost</th></tr></thead><tbody>{rows}</tbody></table></div><h3>Đối chiếu từng case</h3><div style="overflow-x:auto"><table><thead><tr><th>Case</th><th>Method</th><th>Status</th><th>Answer / 2</th><th>Context / 2</th><th>Abstention</th><th>Model answer / error</th><th>Review reason</th></tr></thead><tbody>{case_rows}</tbody></table></div></section>
<section><h2>Dev và cách chọn</h2><p>Dev gồm 20 câu trả lời được, 2 câu thiếu bằng chứng; 5 phương pháp được đo trước khi khóa cấu hình. Chọn theo answer grade mean (0–2, lỗi tính 0), rồi abstention đúng, context evidence, latency. BM25 lexical được chọn. Runtime errors được tính answer grade 0; context/retrieval metrics được đo trên dữ liệu trace và dùng toàn bộ mẫu số answerable.</p><div style="overflow-x:auto"><table><thead><tr><th>Method</th><th>Hit@1</th><th>Hit@3</th><th>Context</th><th>Answer 0/1/2; mean</th><th>Context 0/1/2</th><th>Citation support</th><th>Answered w/citation</th><th>Tool use*</th><th>Search count distribution</th><th>Abstain</th><th>False abstain</th><th>Errors</th><th>Median s</th><th>Total s</th><th>Tokens</th><th>Cost</th></tr></thead><tbody>{dev_html}</tbody></table></div><h3>Thiết kế cấu hình</h3><div style="overflow-x:auto"><table><thead><tr><th>Method</th><th>Retrieval</th><th>Top-k</th><th>Candidates</th><th>Budget</th><th>Max searches</th><th>Hypothesis</th></tr></thead><tbody>{config_html}</tbody></table></div><p class="muted">BM25 thử khớp từ vựng chính xác và context lớn hơn; hybrid thử gộp dense + BM25 bằng RRF. Đây là các gói cấu hình, chưa tách ablation theo từng thay đổi. Hai mươi trace đã xem trước được phân loại lại thành dev, không phải holdout độc lập.</p></section>
<section><h2>Năm phương pháp</h2><ol><li>Dense cosine với vector BGE Day 06.</li><li>BM25 lexical cho OCR tiếng Việt.</li><li>Hybrid dense + BM25 bằng reciprocal-rank fusion.</li><li>MMR giảm trùng lặp trong shortlist.</li><li>Hybrid shortlist rồi rerank bằng MiniLM cross-encoder.</li></ol></section>
<section><h2>Nguồn, giới hạn và file demo</h2><p><a href="../data/nd13/13nd.signed.pdf">PDF Nghị định 13</a> · <a href="../benchmark/nd13/protocol.json">Protocol</a> · <a href="NGHI_DINH_13_DEMO.md">Báo cáo Markdown</a> · <a href="../results/nd13/validation.json">Metrics JSON</a> · <a href="../results/nd13/v2/selection.json">Lựa chọn đã freeze</a>.</p><p>Nguồn là bản ký số năm 2023. OCR còn lỗi nhận dạng. BGE-small-en-v1.5 và MiniLM được giữ từ pipeline Day 06 khi truy xuất tiếng Việt. Review ngữ nghĩa được AI hỗ trợ và cần người học xác nhận. Báo cáo không xác nhận quy định hiện hành và không phải tư vấn pháp lý.</p></section><footer class="muted">Nguồn: Day 06 · Unit tests: {unit['tests_run']}/{unit['tests_run']} pass · Mỗi cấu hình có một lỗi runtime trên test.</footer></main></html>'''
 Path('report/NGHI_DINH_13_DEMO.html').write_text(page,encoding='utf-8')
 print(f"Wrote report/NGHI_DINH_13_DEMO.html and .md; selected={selection['selected']}; tests={unit['tests_run']}")

if __name__=='__main__': main()
