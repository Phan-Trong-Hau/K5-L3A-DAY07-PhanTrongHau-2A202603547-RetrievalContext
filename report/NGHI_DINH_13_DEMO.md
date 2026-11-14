# Demo: Agentic RAG trên Nghị định 13/2023/NĐ-CP

## Mục tiêu

So sánh năm phương pháp retrieval trên tài liệu tiếng Việt của Day 06, chọn cấu hình chỉ bằng dev, rồi đánh giá một lần trên test mới. Bản PDF ký số năm 2023 được giữ nguyên cùng OCR, chunks và vector Day 06. Không dùng bài Alice cho benchmark này.

## Thiết kế benchmark

- Dev: 22 câu, 20 có đáp án và 2 câu cố ý không có bằng chứng; dùng so sánh 5 phương pháp.
- Test đóng băng: 7 câu mới, 5 có đáp án và 2 thiếu bằng chứng; chỉ chạy baseline và phương pháp được chọn trên dev.
- Hai mươi câu đã chạy và xem trước ở phiên trước được lưu dưới `results/nd13/external_v1/` và dùng lại làm dev; chúng không được tính là holdout độc lập.
- Quy tắc chọn: điểm answer grade trung bình trên dev (0–2; lỗi chạy tính 0), sau đó lần lượt xét abstention đúng, evidence trong context, latency.
- BM25 tiếng Việt (`lexical`) được chọn trên dev. Model: Qwen 3 4B local; corpus và code được hash/freeze trước test.

## Kết quả test mới

| Cấu hình | Answer grade TB / 2 (lỗi=0) | Đúng hoàn toàn | Gold evidence trong context | Từ chối đúng câu thiếu evidence | Lỗi | Median giây |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 0.40/2 | 1/5 | 1/5 | 2/2 | 1 | 7.3 |
| lexical | 1.40/2 | 3/5 | 4/5 | 2/2 | 1 | 18.0 |

BM25 trả lời đúng về nội dung ở 4/5 câu có đáp án, nhưng chỉ 3/4 citation được hỗ trợ đúng đoạn; ở `nd13-23`, câu trả lời nêu đúng điều kiện nhưng citation trỏ sang trang 15 thay vì đoạn luật ở trang 11, nên được chấm answer 1/2. BM25 từ chối đúng 2/2 câu không có bằng chứng. Câu `nd13-25` là lỗi giao thức: model lấy đúng đoạn trang 21 cho thấy kiểm tra thường niên và ngoại lệ, nhưng lại phát abstain mà không gọi retrieval theo giao thức; lượt sửa cũng bỏ retrieval nên runner ghi `error`. Điểm câu này là 0, không che lỗi bằng hit@3. Baseline trả lời đúng 1/5 câu, từ chối đúng 2/2 câu thiếu evidence, và có một lỗi giao thức.

### Chấm từng câu

| Case | Method | Trạng thái | Answer / 2 | Context / 2 | Abstention |
|---|---|---|---:|---:|---|
| nd13-21 | baseline | abstain | 0 | 0 | — |
| nd13-22 | baseline | abstain | 0 | 0 | — |
| nd13-23 | baseline | abstain | 0 | 0 | — |
| nd13-24 | baseline | answered | 2 | 2 | — |
| nd13-25 | baseline | error | 0 | 0 | — |
| nd13-test-missing-03 | baseline | abstain | — | — | đúng |
| nd13-test-missing-04 | baseline | abstain | — | — | đúng |
| nd13-21 | lexical | answered | 2 | 2 | — |
| nd13-22 | lexical | answered | 2 | 2 | — |
| nd13-23 | lexical | answered | 1 | 2 | — |
| nd13-24 | lexical | answered | 2 | 2 | — |
| nd13-25 | lexical | error | 0 | 0 | — |
| nd13-test-missing-03 | lexical | abstain | — | — | đúng |
| nd13-test-missing-04 | lexical | abstain | — | — | đúng |

## So sánh dev dùng để chọn

| Method | Answer grade TB / 2 (lỗi=0) | Từ chối nhầm / câu có đáp án | Gold evidence trong context | Từ chối đúng / câu thiếu evidence | Lỗi | Median giây |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 0.50/2 | 14/20 | 5/20 | 2/2 | 0 | 7.7 |
| lexical | 1.30/2 | 2/18 | 20/20 | 2/2 | 2 | 16.6 |
| hybrid | 1.00/2 | 5/20 | 15/20 | 2/2 | 0 | 20.9 |
| mmr | 0.95/2 | 8/20 | 11/20 | 2/2 | 0 | 16.3 |
| rerank | 1.30/2 | 3/20 | 17/20 | 2/2 | 0 | 27.9 |

## Năm phương pháp

1. Dense cosine trên vector BGE Day 06.
2. BM25 lexical trên OCR tiếng Việt.
3. Hybrid dense + BM25 bằng reciprocal-rank fusion.
4. MMR giảm các đoạn trùng lặp trong shortlist dense.
5. Rerank shortlist hybrid bằng MiniLM cross-encoder.

## Kiểm tra và giới hạn

**Unit tests: 46/46 pass.** Đây là kiểm tra code bằng mock/fake provider, không đại diện chất lượng trả lời thực tế. Test end-to-end không pass hết: BM25 có một lỗi protocol trên `nd13-25`; kết quả được giữ nguyên trong report.

Dev/test là benchmark nội bộ nhỏ, phần review ngữ nghĩa có hỗ trợ AI và cần người học xác nhận. OCR có lỗi nhận dạng. BGE-small-en-v1.5 và MiniLM là model có tên tiếng Anh được giữ từ pipeline Day 06 khi xử lý tiếng Việt. Nguồn là văn bản năm 2023, không xác nhận quy định hiện hành và không phải tư vấn pháp lý.

## Artifact để demo

- Protocol: `benchmark/nd13/protocol.json`
- Câu hỏi: `benchmark/nd13/dev.json`, `benchmark/nd13/test.json`
- Chọn cấu hình và hash: `results/nd13/v2/selection.json`
- Trace test: `results/nd13/v2/test/<method>/traces.json`
- Report dữ liệu: `results/nd13/validation.json`
- PDF nguồn: `data/nd13/13nd.signed.pdf`

Chạy lại code tests: `python3 scripts/check_tests.py`. Chạy viewer trace: `.venv/bin/python scripts/demo.py --scenario all`.
