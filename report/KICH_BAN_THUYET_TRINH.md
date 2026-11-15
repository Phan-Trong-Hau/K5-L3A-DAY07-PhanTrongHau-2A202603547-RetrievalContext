# Kịch bản demo và thuyết trình — Nghị định 13

**Người trình bày:** Phan Trọng Hậu · 2A202603547 · L3A
**Thời lượng gợi ý:** 8–10 phút, trong đó 2 phút replay trace.
**Tài liệu chính:** [Báo cáo demo HTML](NGHI_DINH_13_DEMO.html) · [Báo cáo Markdown](NGHI_DINH_13_DEMO.md).

## Chuẩn bị

1. Mở `report/NGHI_DINH_13_DEMO.html` và `results/nd13/v2/selection.json`.
2. Từ thư mục gốc repo, chạy `.venv/bin/python scripts/demo.py --scenario all`.
3. Đây là replay trace đã lưu, không phải suy luận live. Không cần Ollama để trình bày.
4. Nguồn là Nghị định 13 tiếng Việt từ Day 06. Không mở ví dụ Alice trong phần demo này.

## Kịch bản 8–10 phút

### 0–1 phút: mục tiêu

> Em xây dựng agentic RAG tiếp nối dữ liệu Day 06. Bài tập yêu cầu agent tìm bằng chứng, trả lời có nguồn và nhận biết khi tài liệu không có câu trả lời. Em dùng Nghị định 13/2023/NĐ-CP bằng tiếng Việt.

### 1–2 phút: dữ liệu và kiến trúc

> Pipeline dùng lại PDF ký số, OCR, chunks và vector 384 chiều của Day 06. Dense truy vấn qua Qdrant; các nhánh khác là BM25 tiếng Việt, hybrid RRF, MMR và cross-encoder rerank. Qwen 3 4B chạy local với Ollama để gọi search tool và tạo câu trả lời/citation.

Lưu ý: PDF là nguồn năm 2023; OCR còn lỗi. Đây không phải khẳng định quy định hiện hành hay tư vấn pháp lý.

### 2–3 phút: benchmark và cách chọn

> Dev có 22 câu: 20 câu có đáp án và 2 câu thiếu bằng chứng. Năm phương pháp được so sánh trên dev. Test đóng băng có 7 câu mới: 5 có đáp án và 2 thiếu bằng chứng. Trên test chỉ chạy baseline và phương pháp được chọn từ dev.
>
> Hai mươi câu cũ đã từng được xem, nên được chuyển sang dev; chúng không được tính là test độc lập. Trên dev, BM25 được chọn theo answer grade, lỗi tính 0, rồi tie-break theo abstention, context evidence và latency.

### 3–5 phút: cải thiện và retrieval

> Dense giữ vector Day 06. BM25 thử khớp cụm từ OCR chính xác và context lớn hơn; hybrid thử gộp dense và BM25 bằng RRF. MMR và rerank mở rộng so sánh. Trên dev, lexical đạt answer grade mean 1.30/2, có evidence trong context ở 20/20 câu trả lời được và có 2 lỗi runtime. Rerank cũng đạt 1.30 nhưng evidence context 17/20; tie-break chọn lexical.

Đây là so sánh theo gói cấu hình; chưa tách ablation ảnh hưởng riêng của context budget. Phí dịch vụ model là 0 USD vì chạy local, chưa tính điện/phần cứng.

### 5–7 phút: replay test

Chạy:

```bash
.venv/bin/python scripts/demo.py --scenario improvement
.venv/bin/python scripts/demo.py --scenario failure
.venv/bin/python scripts/demo.py --scenario abstention
```

> Ví dụ cải thiện so sánh baseline và BM25 ở câu 72 giờ. BM25 tìm evidence và trả lời đúng. Ví dụ lỗi `nd13-25`: đánh giá ranking query gốc ngoài lượt agent tìm thấy evidence trang 21, nhưng agent bỏ qua retrieval bắt buộc, context cuối rỗng và runner ghi `error`. Ranking ngoại tuyến không được tính là retrieval thành công của agent. Đây là lỗi, được tính answer grade 0.
>
> Ở `nd13-23`, nội dung trả lời nêu đúng điều kiện an toàn/sức khỏe, nhưng citation lại trỏ trang 15 trong khi bằng chứng nằm trang 11. Vì vậy case chỉ được chấm 1/2, và chỉ 3/4 citation test của BM25 được xác nhận hỗ trợ claim.
>
> Với hai câu test không có bằng chứng, BM25 từ chối đúng 2/2. Baseline cũng từ chối đúng 2/2. Cả hai cấu hình vẫn có một lỗi protocol trên nhóm câu có đáp án.

### 7–8 phút: kết quả và giới hạn

> BM25 đạt answer grade mean 1.40/2 trên toàn bộ 5 câu test có đáp án khi lỗi tính 0; có 3 câu đạt grade 2, một câu grade 1 vì citation sai trang, một lỗi runtime. Context có evidence ở 4/5, Evidence Hit@3 là 5/5, và abstention đúng 2/2 câu thiếu bằng chứng. Vì vậy không thể gọi toàn bộ test là pass.
>
> Có 52/52 unit tests pass trong lần chạy 15/11/2026. Chúng kiểm tra code/mock, không chứng minh chất lượng câu trả lời thật. Nhãn ngữ nghĩa có AI hỗ trợ và học viên cần rà lại trước khi nộp.

## Câu hỏi thường gặp

**Tại sao test là 7 câu?** Benchmark cơ bản cần ít nhất 5 câu có đáp án và 2 câu thiếu bằng chứng; test mới đáp ứng đúng ngưỡng đó. Dev có 20+2, vượt mức tối thiểu 15+2.

**Tại sao không chạy đủ 5 phương pháp trên test?** Phương pháp phải được chọn bằng dev. Chạy cả năm trên test và dùng chúng để so/điều chỉnh sẽ biến test thành dev. Baseline và phương pháp đã chọn được so sánh trên holdout.

**Citation đúng ID có đồng nghĩa câu trả lời có căn cứ?** Không. ID phải nằm trong context và đoạn được trích phải hỗ trợ từng claim. `nd13-23` cho thấy citation có thể trỏ sai trang.

**Tại sao giữ lỗi thay vì sửa rồi báo lại?** Sau khi xem lỗi test, chỉnh hệ thống rồi chạy lại cùng câu hỏi sẽ làm test bị dùng để phát triển. Cần tạo test mới nếu muốn xác nhận một thay đổi.

**Đã làm bonus 100 trang chưa?** Đã thử với báo cáo tiếng Việt *Việt Nam 2035* (584 trang), nhưng chưa hoàn thành rubric bonus. Test độc lập đạt 25/30 (83,3%), dưới ngưỡng 27/30; V4 không được chọn vì dev thấp hơn V3. Tám hình được kiểm tra thủ công, chưa đủ bao phủ hình ảnh của cả tài liệu. Xem [report bonus HTML](BONUS_TRIAL.html) để biết từng lỗi và giới hạn.

## Các file nên mở khi trả lời sâu

- [Benchmark protocol](../benchmark/nd13/protocol.json)
- [Dev/test metrics và audit](../results/nd13/validation.json)
- [Lựa chọn freeze](../results/nd13/v2/selection.json)
- [Test trace lexical](../results/nd13/v2/test/lexical/traces.json)
- [Test reviews lexical](../results/nd13/v2/test/lexical/reviews.json)
- [Hướng dẫn chạy](../docs/ND13.md)
