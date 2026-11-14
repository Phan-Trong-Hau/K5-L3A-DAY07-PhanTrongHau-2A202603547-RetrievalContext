"""Render the Vietnamese submission report from real traces and explicit audit labels."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.common import load


def fraction(metric):
    if metric['N'] == 0:
        return '0/0 (N/A)'
    return f"{metric['n']}/{metric['N']} ({metric['rate']:.1%})"


def compact(text):
    import re
    return re.sub(r'\b[0-9a-f]{64}\b', lambda m: m.group(0)[:12] + '…', text).replace('|', '\\|').replace('\n', ' ')


def main():
    selection = load('results/selection.json')
    winner = selection['selected']
    configs = load('configs/experiments.json')
    dev = load('results/dev/comparison.json')
    test = load('results/test/comparison.json')
    provenance = load('data/day6/provenance.json')
    baseline_traces = {t['query_id']: t for t in load('results/dev/baseline/traces.json')}
    selected_traces = {t['query_id']: t for t in load(f'results/dev/{winner}/traces.json')}
    final_traces = load(f'results/test/{winner}/traces.json')
    n_answerable = sum(t['answerable'] for t in final_traces)
    n_missing = sum(not t['answerable'] for t in final_traces)
    n_missing_errors = sum(not t['answerable'] and t['status'] == 'error' for t in final_traces)
    lines = [
        '# Báo cáo Day 7 — Agentic RAG', '',
        '**Phan Trọng Hậu · 2A202603547 · L3A**', '',
        f"Cấu hình được chọn trên dev: **{winner}**. Test có **{test[winner]['answer_grades']['2']}/{n_answerable} câu có đáp án đạt grounded grade 2**. "
        f"Trong {n_missing} câu thiếu evidence, có **{n_missing_errors} lỗi giao thức**; model từ chối trước khi gọi retrieval. "
        'Không tính các lỗi này là abstention đúng. Đã giữ nguyên code/config sau freeze và báo cả kết quả không đạt.', '',
        '## Dữ liệu và benchmark', '',
        '- Corpus: *Alice’s Adventures in Wonderland*, Lewis Carroll; [Project Gutenberg #11](https://www.gutenberg.org/ebooks/11). Bản tải gốc và giấy phép giữ trong `data/day6/alice.txt`.',
        '- Tiếp nối collection **C** Day 6: **192 chunk, 82 đơn vị trang logic**, giữ nguyên ID/text/nguồn/page/metadata và vector. Đây không phải PDF 82 trang. Không làm bonus tài liệu từ 100 trang.',
        '- Dense: Qdrant local, exact cosine, **BAAI/bge-small-en-v1.5**, **384 chiều**, FastEmbed 0.9.1. Query dùng `query_embed` tương thích Day 6; không re-embed tài liệu. Snapshot ONNX/tokenizer được đối chiếu SHA-256.',
        '- Agent thật: **qwen3:4b-instruct**, Q4_K_M, Ollama local; temperature 0, seed 7, cửa sổ 8192 token, tối đa 384 token sinh/lượt. Máy đo: NVIDIA GTX 1650 4 GB, CPython 3.14.9. Model digest: `' + selection['model_digest'] + '`.',
        '- Dev: 15 câu có đáp án tái dùng từ Day 6 + 2 câu thiếu evidence mới. Test: **5 câu có đáp án mới + 2 câu thiếu evidence mới**, không dùng lại test Day 6. Tổng cộng **24 câu**. Câu hỏi tiếng Anh phù hợp corpus/embedding tiếng Anh.',
        '- Gold gồm nguồn, trang logic, trích đoạn nguyên văn; mỗi câu có một đoạn evidence đủ trong một chunk. Câu thiếu evidence được kiểm tra bằng quét toàn corpus và đọc cảnh liên quan; xem `benchmark/absence_audit.json`.',
        '- Gold/expected answer chỉ vào evaluation sau generation; agent chỉ nhận question và filter người dùng nêu rõ. Chương III/VI/IX/VIII/XI chỉ được lọc khi câu hỏi đã ghi chương, áp dụng giống nhau cho cả ba phương pháp.',
        '- Nhãn do **Codex hỗ trợ đọc đối chiếu trace và nguồn**, có reviewer/lý do trong `reviews.json`; chưa phải xác nhận thủ công của học viên. Người học cần rà lại trước nộp. Không dùng mock hoặc tự gán expected answer làm output model.', '',
        '## Retrieval, context và thử nghiệm', '',
        'Baseline dense giữ cơ chế cosine Day 6, context 1.200 ký tự và một lượt search. '
        'Cải thiện 1 dùng BM25 (`k1=1.5`, `b=0.75`), context 4.800 ký tự và tối đa hai search để giữ thêm đoạn và thử lại query. '
        'Cải thiện 2 dùng hybrid RRF (`k=60`, 20 candidate mỗi nhánh), cùng budget/lượt với lexical để kết hợp semantic và từ khóa. '
        'Hai cấu hình cải thiện đồng thời là phương pháp retrieval thứ hai và thứ ba. Đây là so sánh theo gói cấu hình, chưa phải ablation từng thành phần.', '',
        '| Cấu hình | Method / top-k / budget ký tự / search | Split | Hit@1 | Evidence Hit@3 | Context Evidence Rate | Median giây/câu | Tổng giây agent | Phí dịch vụ |',
        '|---|---|---|---|---|---|---|---|---|',
    ]
    for split, comparison in [('dev', dev), ('test', test)]:
        for name in (['baseline', 'lexical', 'hybrid'] if split == 'dev' else ['baseline', winner]):
            if split == 'test' and name == 'baseline' == winner and len(comparison) == 1 and any('| baseline |' in x and '| test |' in x for x in lines):
                continue
            c, s = configs[name], comparison[name]
            lines.append(f"| {name}{' (chọn)' if name == winner else ''} | {c['method']} / {c['top_k']} / {c['budget']} / {c['max_searches']} | {split} | {fraction(s['hit1'])} | {fraction(s['hit3'])} | {fraction(s['context_evidence'])} | {s['median_seconds']:.2f} | {s['total_seconds']:.2f} | 0 USD |")
    lines += ['', 'Hit@1/3 đo ranking **query gốc** tại cùng cutoff 1/3. Query viết lại và kết quả từng tool được lưu riêng. '
              'Context Evidence Rate đo context cuối thật sự gửi model; không suy từ top-3 query gốc. '
              'Budget gồm cả header ID/nguồn/trang. Context giữ chunk nguyên vẹn, loại trùng và hợp nhất rank qua lượt tìm; '
              'chunk không vừa bị bỏ. Phí API 0 USD do chạy local, **không** bao gồm điện/phần cứng. '
              'Median/tổng trên là thời gian vòng agent, không gồm nạp index và lượt kiểm tra ranking gốc sau generation.', '',
              'Thứ tự chạy dev: baseline → lexical → hybrid, dùng lại model/query-embedding cache trong một tiến trình. '
              'Latency phản ánh điều kiện cache hỗn hợp; không phải phép so sánh cold-start cô lập. '
              'Context lớn hơn có thể tăng prompt cost/latency; giới hạn hai lượt search không có nghĩa model luôn dùng hết.', '',
              '## Hai lỗi dev và kết quả trước/sau', '']
    cases = {q['id']: q for q in load('benchmark/dev.json')}
    for qid in ['q04', 'q06']:
        before, after = baseline_traces[qid], selected_traces[qid]
        lines += [f"### {qid}: {cases[qid]['question']}", '',
                  f"- Baseline: **{before['status']}**; context evidence **{before['context_hit']}**. {compact(before['answer'])}",
                  f"- Cấu hình chọn `{winner}`: **{after['status']}**; context evidence **{after['context_hit']}**. {compact(after['answer'])}"]
        if qid == 'q04':
            lines += ['- Nguyên nhân: dense query gốc có hit, nhưng query model thêm tên truyện làm ranking chuyển sang đoạn kể chuyện ở bàn trà. Đây là lỗi query transformation; chỉ tăng budget không đảm bảo khôi phục bằng chứng đã rớt khỏi candidate. BM25/hybrid được thử để giữ các từ khóa cake/words.', '']
        else:
            lines += ['- Nguyên nhân: tool dense tìm thấy p15 (Alice phát comfits) trước p16 (Dodo tặng thimble). Context 1.200 ký tự giữ p15 rồi không đủ chỗ cho p16. Model suy diễn sai từ việc thiếu đoạn kế tiếp. Hai cấu hình context lớn hơn được đo lại để kiểm tra khả năng giữ evidence đúng.', '']
    lines += ['### Lỗi còn lại và giới hạn', '',
              'Dev `q13` cho thấy retrieval/context có thể chứa đủ danh sách bốn nhánh Arithmetic nhưng model từ chối vì cho rằng đó không phải toán học thật. '
              'Cần phân biệt nội dung hư cấu trong truyện với kiến thức đời thực. Đây là lỗi reasoning/grounding, không thể kết luận chỉ từ citation ID hợp lệ. '
              'Các nhãn và kết quả không cải thiện vẫn giữ nguyên trong bảng và trace.', '',
              'Lexical `q14` còn minh họa lỗi citation: model nói đúng old conger-eel/once a week nhưng cite `aa49e3…` ở p82 '
              '(chị Alice tưởng tượng em lớn lên), trong khi evidence nằm ở p62. ID có trong context nhưng không hỗ trợ đáp án. '
              'Theo protocol đòi được citation hỗ trợ, answer grade là 0 và citation support là false. '
              'Giữ nguyên ID SHA-256 Day 6 giúp truy vết. ID dài hoặc cách model chọn nguồn là các giả thuyết cho lỗi này; chưa có ablation để xác định nguyên nhân.', '',
              '## Chọn trên dev, đánh giá test sau freeze', '',
              'Điểm dev dùng để chọn (lỗi câu có đáp án tính 0): ' + '; '.join(
                  f"**{name}: {dev[name]['selection_mean_errors_zero']:.3f}/2**" for name in ['baseline', 'lexical', 'hybrid']) + '. '
              'Mean chất lượng trên lượt thành công ở bảng dưới có thể cao hơn vì loại riêng lỗi; không dùng mean đó để ưu ái cấu hình có lỗi.', '',
              f"Chọn **{winner}**, chốt lúc **{selection['frozen_at']}**. Tiêu chí công bố trước: tối đa grounded-answer mean dev (lỗi tính 0 khi chọn), "
              'rồi tỷ lệ abstention đúng, context evidence, median thời gian thấp hơn và tên cấu hình. '
              'File `results/selection.json` lưu tiêu chí, toàn bộ dev comparison và hash code/config/model/corpus/dev/test/reviews. '
              'Sau freeze chỉ chạy baseline và winner trên cùng test; không thay code/config theo test.', '',
              '## Agent và đánh giá câu trả lời', '',
              'Model dùng native `search_documents`, có thể viết lại query và tìm tiếp; kết thúc bằng `submit_answer` hoặc final text. '
              'Phải tìm trước khi kết thúc. Từ chối được model phát ra rõ `ABSTAIN:`; các tham chiếu đoạn liên quan trong raw refusal được bỏ khỏi citation đầu ra, '
              'raw message vẫn giữ trong trace. Lỗi provider/schema/citation không hợp lệ có status `error`, không thay bằng từ chối giả. '
              'Nội dung tài liệu chỉ là dữ liệu. Citation được kiểm tra membership và đọc đối chiếu ngữ nghĩa trong nhãn.', '',
              '| Cấu hình / split | Tool use | Phân bố lượt search | Grounded 0/1/2; mean /2 | Context 0/1/2 | Citation hỗ trợ | Câu trả lời có citation | Abstention đúng | Từ chối nhầm | Lỗi |',
              '|---|---|---|---|---|---|---|---|---|---|']
    for split, comparison in [('dev', dev), ('test', test)]:
        for name, s in comparison.items():
            g, c = s['answer_grades'], s['context_grades']
            mean = 'N/A' if s['grounded_mean'] is None else f"{s['grounded_mean']:.3f}/2"
            dist = ', '.join(f"{n} lượt: {count} câu" for n, count in s['search_count_distribution'].items())
            lines.append(f"| {name} / {split} | {fraction(s['tool_use'])} | {dist} | {g['0']}/{g['1']}/{g['2']}; {mean} | {c['0']}/{c['1']}/{c['2']} | {fraction(s['citation_support'])} | {fraction(s['citation_coverage'])} | {fraction(s['abstention'])} | {fraction(s['false_abstention'])} | {s['errors']} |")
    lines += ['', 'Grounded/context 0/1/2 lần lượt là sai hoặc thiếu / một phần / đủ. Citation hỗ trợ được chấm theo từng citation, '
              'không đồng nhất với đáp án đầy đủ. Lượt lỗi báo riêng; quality mean trên câu có đáp án thành công; tiêu chí chọn phạt lỗi bằng 0.', '',
              'Trong thực nghiệm này, mọi câu đã gọi tool đều chỉ dùng một lượt search dù lexical/hybrid cho phép hai lượt. '
              'Vì vậy chưa có bằng chứng về lợi ích của multi-round; cải thiện đo được đi cùng thay đổi retriever/context, không thể quy cho việc tăng giới hạn số lượt.', '',
              'Hai câu thiếu evidence ở test làm model phát `ABSTAIN` ngay từ lượt đầu, trước bất kỳ tool call nào, '
              'nên runner ghi error thay vì công nhận search-and-abstain. Vì cả hai lượt đều lỗi, abstention quality có mẫu số 0 (N/A), '
              'không phải đạt 100%. Tool use 5/5 trên lượt thành công cũng không che đi 2/7 lượt lỗi. '
              'Đây là giới hạn điều phối đã bộc lộ trên holdout; muốn cải thiện cần tạo test mới và đo lại, không sửa rồi báo lại cùng test như độc lập.', '',
              '## Đọc toàn bộ test: baseline và cấu hình chọn', '',
              'Các ID citation được viết ngắn trong bảng để dễ đọc; ID đầy đủ, context, tool call và nhãn nằm ở liên kết trace. '
              'Đã đối chiếu cả 5 câu có đáp án và 2 câu thiếu evidence cho mỗi cấu hình.', '']
    for name in dict.fromkeys(['baseline', winner]):
        folder = f'results/test/{name}'
        traces = load(folder + '/traces.json')
        reviews = {r['query_id']: r for r in load(folder + '/reviews.json')}
        lines += [f"### {name}", '', f"[Trace](../../{folder}/traces.json) · [Nhãn và lý do](../../{folder}/reviews.json)", '',
                  '| Query | Search | Kết quả | Context / Answer | Nhận xét đối chiếu |', '|---|---|---|---|---|']
        for t in traces:
            r = reviews.get(t['query_id'], {})
            calls = sum(e['event'] == 'search' for e in t['events'])
            grade = f"{r.get('context_grade', 'N/A')} / {r.get('answer_grade', 'N/A')}" if t['answerable'] else f"abstention={r.get('abstention_correct')}"
            lines.append(f"| {t['query_id']} | {calls} | {t['status']}: {compact(t['answer'] or t.get('error', ''))} | {grade} | {compact(r.get('reason', 'Lỗi hệ thống; không chấm thành công.'))} |")
        lines.append('')
    lines += ['## Thời gian, token và tái lập', '',
              '| Cấu hình / split | Prompt token | Completion token | Tổng thời gian agent (s) |', '|---|---|---|---|']
    for split, comparison in [('dev', dev), ('test', test)]:
        for name, s in comparison.items():
            lines.append(f"| {name} / {split} | {s['prompt_tokens']} | {s['completion_tokens']} | {s['total_seconds']:.2f} |")
    lines += ['', 'Token là tổng qua các lượt model, bao gồm context/prompt lặp; không quy đổi ra tiền API. '
              'Thông tin phiên bản và digest mỗi cấu hình nằm ở `environment.json`/`manifest.json`. '
              'Các lượt chạy thử tích hợp trước benchmark chỉ lưu cục bộ, không nằm trong bài nộp và không gộp vào số liệu; tóm tắt ở `results/README.md`.', '',
              '```bash', 'python3 -m unittest discover -s tests -v',
              'uv venv --python 3.14', 'uv pip sync --python .venv/bin/python requirements.lock.txt',
              'ollama pull qwen3:4b-instruct',
              '.venv/bin/python scripts/ask.py "What prize did the Dodo present to Alice?"',
              '.venv/bin/python scripts/reproduce.py --output runs/reproduction-01', '```', '',
              'Xem [hướng dẫn đầy đủ](../../docs/RUNNING.md), [thiết kế](../../docs/IMPLEMENTATION.md), '
              '[protocol](../../benchmark/protocol.json), [dev comparison](../../results/dev/comparison.json), '
              '[test comparison](../../results/test/comparison.json), [freeze](../../results/selection.json).', '',
              'Giới hạn: bộ test nhỏ; nhãn AI hỗ trợ cần người học xác nhận; exact evidence có thể bỏ sót cách diễn đạt/nguồn thay thế; '
              'chưa đánh giá tiếng Việt, multi-hop, reranker hoặc đa phương thức. Không tuyên bố đạt bonus 15 điểm. '
              'Không suy rộng điểm số của bộ này thành độ chính xác trên mọi tài liệu.', '']
    path = Path('report/individual/2A202603547_PhanTrongHau.md')
    path.write_text('\n'.join(lines), encoding='utf-8')
    print(path)


if __name__ == '__main__':
    main()
