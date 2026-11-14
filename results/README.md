# Kết quả thực nghiệm thật

**Bộ đánh giá hiện tại:** `nd13/` có 20 câu tiếng Việt về Nghị định 13, chạy qua
năm phương pháp. `nd13/validation.json` tách lượt agent, hit@3, evidence context,
lỗi và unit tests; xem [báo cáo HTML](../report/NGHI_DINH_13_DEMO.html). Các câu
trong bộ này là external test cố định; không chọn winner theo chúng.

**V2:** `v2/` chứa năm phương pháp, freeze mới, holdout mới và hồi quy các case v1.
`v2/validation.json` tách rõ pass code, pass regression và pass holdout.
Các đường dẫn dưới đây là lịch sử v1, không bị ghi đè khi sửa controller v2.

- `dev/`: cùng 17 câu, ba cấu hình baseline/dense, lexical/BM25, hybrid/RRF.
- `selection.json`: cấu hình được chọn trên dev, thời điểm freeze và checksum.
- `test/`: cùng 7 câu mới, baseline và cấu hình đã chọn, chạy sau freeze.

Mỗi cấu hình có `manifest.json`, `environment.json`, `traces.json`, `summary.json`,
`reviews.json`, `audit_summary.json`. Trace ghi output thật của Qwen local, native
tool calls, query/filter/ranking/context và token/thời gian/lỗi. Nhãn có tên reviewer
AI và lý do đối chiếu, cần người học rà soát trước nộp. Không dùng mock để báo điểm.

`comparison.json` tổng hợp retrieval và nhãn. Citation precision đếm ID nguồn duy
nhất trong mỗi câu trả lời; nhắc lại cùng ID không nhân số nguồn. Abstention đã
chuẩn hóa không có citation đầu ra; raw model message vẫn có trong event.

## Các lần tích hợp trước benchmark

Các trace chạy thử được giữ cục bộ trong `integration_attempt/`, **không đưa vào
commit bài nộp và không gộp vào bảng chất lượng cuối**. Tóm tắt quá trình tích hợp:

- `integration_attempt/native-finish-only/`: 14 câu đã chạy, cả 14 lỗi bộ nhận kết
  quả vì model trả final text thay vì native `submit_answer`. Retrieval vẫn chạy;
  đây là lỗi tích hợp, không phải 14 câu từ chối đúng.
- `integration_attempt/text-format-pilot/`: 17 baseline + 5 lexical. Dừng để chuẩn
  hóa refusal bỏ tham chiếu đoạn liên quan khỏi citation đầu ra, tránh đếm citation
  cho khẳng định thiếu bằng chứng. Sau sửa, chạy lại toàn bộ dev với cùng code cuối.

Không dùng test để sửa các vấn đề tích hợp này. Mọi quyết định/sửa code xảy ra trên
dev trước `selection.json`.
