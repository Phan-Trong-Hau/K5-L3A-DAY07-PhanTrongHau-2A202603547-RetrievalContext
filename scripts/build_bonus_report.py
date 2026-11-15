#!/usr/bin/env python3
"""Build an offline HTML progress report without inventing missing results."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    data = json.loads((ROOT / 'data/bonus/vietnam2035/index_manifest.json').read_text(encoding='utf-8'))
    metrics = json.loads((ROOT / 'results/bonus/dev_bm25_k3/metrics.json').read_text(encoding='utf-8'))
    new_metrics = json.loads((ROOT / 'results/bonus/dev_caption_v2/metrics.json').read_text(encoding='utf-8'))
    test_metrics = json.loads((ROOT / 'results/bonus/test_caption_draft/metrics.json').read_text(encoding='utf-8'))
    runtime = json.loads((ROOT / 'results/bonus/test_caption_draft/runtime.json').read_text(encoding='utf-8'))
    v4_dev_metrics = json.loads((ROOT / 'results/bonus/dev_v4/metrics.json').read_text(encoding='utf-8'))
    v4_dev_runtime = json.loads((ROOT / 'results/bonus/dev_v4/runtime.json').read_text(encoding='utf-8'))
    fresh_metrics = json.loads((ROOT / 'results/bonus/test_v3_fresh/metrics.json').read_text(encoding='utf-8'))
    fresh_runtime = json.loads((ROOT / 'results/bonus/test_v3_fresh/runtime.json').read_text(encoding='utf-8'))
    fresh_reviews = json.loads((ROOT / 'results/bonus/test_v3_fresh/reviews.json').read_text(encoding='utf-8'))
    fresh_questions = {x['id']: x for x in json.loads((ROOT / 'benchmarks/bonus/test_fresh_v3.json').read_text(encoding='utf-8'))}
    reviews = json.loads((ROOT / 'results/bonus/dev_bm25_k3/reviews.json').read_text(encoding='utf-8'))
    q = {x['id']: x for x in json.loads((ROOT / 'benchmarks/bonus/dev_draft.json').read_text(encoding='utf-8'))}
    esc = html.escape
    rows = ''.join('<tr><td>'+esc(r['id'])+'</td><td>'+esc(q[r['id']]['category'])+
                   '</td><td>'+('Đạt' if r['pass'] else 'Không đạt')+'</td><td>'+esc(r['reason'])+
                   '</td><td>'+esc(r['evidence_checked'])+'</td></tr>' for r in reviews)
    fresh_rows = ''.join('<tr><td>'+esc(r['id'])+'</td><td>'+esc(fresh_questions[r['id']]['category'])+
                   '</td><td>'+('Đạt' if r['pass'] else 'Không đạt')+'</td><td>'+esc(r['reason'])+
                   '</td><td>'+esc(r['evidence_checked'])+'</td></tr>' for r in fresh_reviews)
    output = f'''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bonus Việt Nam 2035 — kết quả thăm dò</title><style>
:root{{color-scheme:light}}body{{margin:0;background:#f1f5f7;color:#172b3c;font:16px/1.6 system-ui,sans-serif}}
header{{background:#10283d;color:#fff;padding:32px max(calc((100vw - 1050px)/2),24px)}}
main{{max-width:1050px;margin:auto;padding:20px}}section{{background:white;border:1px solid #dce5ea;border-radius:12px;padding:22px;margin:18px 0}}
.alert{{background:#fff2dc;border-left:5px solid #a25d00;padding:14px}}table{{width:100%;border-collapse:collapse;font-size:.9rem}}
th,td{{border:1px solid #dce5ea;text-align:left;padding:8px;vertical-align:top}}th{{background:#e8f1f4}}.scroll{{overflow-x:auto}}a{{color:#185c87}}
</style><header><small>DAY 07 · AGENTIC RAG</small><h1>Bonus: Việt Nam 2035</h1><p>Kết quả thăm dò và giới hạn hiện tại</p></header><main>
<div class="alert"><strong>Chưa đạt điều kiện bonus.</strong> Test độc lập mới nhất đạt {fresh_metrics['all']['pass']}/{fresh_metrics['all']['total']} ({100*fresh_metrics['all']['pass']/fresh_metrics['all']['total']:.1f}%), dưới ngưỡng 90% (cần 27/30). Bộ test này đã được tạo và đóng băng trước lượt dev V3; từng câu đã được đối chiếu với PDF gốc.</div>
<section><h2>Tài liệu và xử lý</h2><p><a href="https://documents.worldbank.org/curated/en/462881491821948950/pdf/103435-v2-VIETNAMESE-PUBLIC-PUBDATE-11-30-2016.pdf">Việt Nam 2035, bản PDF tiếng Việt</a> của World Bank và Bộ Kế hoạch và Đầu tư, 2016. Trích xuất được chữ từ {data['indexed_pages']}/{data['pdf_pages']} trang; số trang dẫn nguồn là trang vật lý của PDF.</p><p>Chỉ mục CLIP có đủ 584 trang và 2.920 vùng, nhưng truy vấn thử một biểu đồ không tìm thấy đúng trang trong 10 kết quả đầu. Nội dung trực quan toàn tài liệu chưa được kiểm chứng đầy đủ.</p></section>
<section><h2>Dev dự thảo</h2><p>BM25 đạt <strong>{metrics['all']['pass']}/{metrics['all']['total']}</strong> câu; cấu hình ưu tiên nhãn đạt <strong>{new_metrics['all']['pass']}/{new_metrics['all']['total']}</strong>. Cả hai lượt không có lỗi hệ thống; đã kiểm tra thủ công. Đây không phải kết quả test bonus.</p><p>Bảng sau là chi tiết BM25:</p><div class="scroll"><table><thead><tr><th>ID</th><th>Nhóm</th><th>Kết quả</th><th>Lý do</th><th>Đối chiếu PDF</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section><h2>Test dự thảo: {test_metrics['all']['pass']}/{test_metrics['all']['total']}</h2><p>Bảng {test_metrics['table']['pass']}/{test_metrics['table']['total']}; ảnh {test_metrics['image']['pass']}/{test_metrics['image']['total']}; biểu đồ {test_metrics['chart']['pass']}/{test_metrics['chart']['total']}; multi-hop {test_metrics['multi_hop']['pass']}/{test_metrics['multi_hop']['total']}; text {test_metrics['text']['pass']}/{test_metrics['text']['total']}; thiếu bằng chứng {test_metrics['unanswerable']['pass']}/{test_metrics['unanswerable']['total']}. Không có lỗi hệ thống; thời gian cộng dồn {runtime['elapsed_seconds_sum']:.1f} giây; chi phí dịch vụ 0 USD (chưa tính điện, phần cứng).</p><p>Các lỗi gồm nhầm cột và đơn vị, không đọc được màu trên hình, diễn giải sai tỷ trọng, từ chối khi có đáp án và thêm thông tin sai khi từ chối.</p><p><a href="../results/bonus/test_caption_draft/reviews.json">Xem đối chiếu từng câu</a> · <a href="../results/bonus/test_caption_draft/metrics.json">Metrics</a> · <a href="../results/bonus/test_caption_draft/runtime.json">Thời gian và token</a></p></section>
<section><h2>Dev V4 — không chọn</h2><p>V4 đạt {v4_dev_metrics['all']['pass']}/{v4_dev_metrics['all']['total']} trên dev, thấp hơn V3 đã chọn (17/18). Hai lỗi: câu Hình 2.11 gắn nhầm hàng dệt vào nhóm doanh thu; câu về 3,2% thêm nội dung không liên quan và kết thúc bằng câu từ chối mâu thuẫn. Không chạy V4 trên test. Thời gian {v4_dev_runtime['elapsed_seconds_sum']:.1f} giây, {v4_dev_runtime['model_calls']} lượt gọi model, không lỗi hệ thống. <a href="../results/bonus/dev_v4/reviews.json">Review V4</a> · <a href="../results/bonus/dev_v4/metrics.json">Metrics</a></p></section>
<section><h2>Test độc lập V3: {fresh_metrics['all']['pass']}/{fresh_metrics['all']['total']}</h2><p>Bảng {fresh_metrics['table']['pass']}/{fresh_metrics['table']['total']}; ảnh/sơ đồ {fresh_metrics['image']['pass']}/{fresh_metrics['image']['total']}; biểu đồ {fresh_metrics['chart']['pass']}/{fresh_metrics['chart']['total']}; multi-hop {fresh_metrics['multi_hop']['pass']}/{fresh_metrics['multi_hop']['total']}; văn bản {fresh_metrics['text']['pass']}/{fresh_metrics['text']['total']}; thiếu bằng chứng {fresh_metrics['unanswerable']['pass']}/{fresh_metrics['unanswerable']['total']}. Lỗi hệ thống {fresh_runtime['errors']}; thời gian {fresh_runtime['elapsed_seconds_sum']:.1f} giây; {fresh_runtime['model_calls']} model calls; chi phí dịch vụ 0 USD (chạy Ollama cục bộ, chưa tính điện và phần cứng).</p><p>Lỗi: V3 từ chối câu tổng hợp hai bảng dù context có đủ bằng chứng; nhầm vị trí bản đồ dưới trái Hình 4.18; thêm mẫu số không được chứng minh khi đọc Hình 5.4; và một lỗi giao thức khi từ chối câu hỏi thiếu dữ liệu. Một câu trả lời hình đúng về mặt hình gốc nhưng context được truy xuất không nêu thứ hạng lưu vực nên bị chấm không đạt theo tiêu chuẩn evidence-grounded.</p><div class="scroll"><table><thead><tr><th>ID</th><th>Nhóm</th><th>Kết quả</th><th>Lý do</th><th>Đối chiếu PDF gốc</th></tr></thead><tbody>{fresh_rows}</tbody></table></div><p><a href="../results/bonus/test_v3_fresh/reviews.json">Review từng câu</a> · <a href="../results/bonus/test_v3_fresh/metrics.json">Metrics</a> · <a href="../results/bonus/test_v3_fresh/runtime.json">Runtime/token</a> · <a href="../benchmarks/bonus/test_fresh_v3.json">Câu hỏi và gold</a></p></section>
<section><h2>Việc còn lại</h2><p>Khắc phục các lỗi V3; kiểm chứng thêm nội dung trực quan toàn tài liệu và đánh giá mức bao phủ hữu ích; sau khi chọn cấu hình chỉ trên dev, đóng băng và chạy một test độc lập mới. Chưa thể nhận 15 điểm bonus từ kết quả hiện có.</p><p><a href="../benchmarks/bonus/README.md">Benchmark dự thảo</a> · <a href="../results/bonus/dev_bm25_k3/reviews.json">Nhãn dev</a> · <a href="../data/bonus/vietnam2035/README.md">Nguồn và cách tái tạo</a></p></section></main></html>'''
    target = ROOT / 'report/BONUS_TRIAL.html'
    target.write_text(output, encoding='utf-8')
    print(target)


if __name__ == '__main__':
    main()
