# Cách chạy và xem kết quả

## Bộ bài nộp hiện tại

Bài dùng Nghị định 13 tiếng Việt và snapshot Day 06. Benchmark v2 có dev 22 câu trên năm phương pháp, test mới 7 câu (5 có đáp án, 2 thiếu evidence), chạy baseline và phương pháp lexical đã chọn từ dev. Xem [protocol](../benchmark/nd13/protocol.json), [report HTML](../report/NGHI_DINH_13_DEMO.html), [báo cáo cá nhân](../report/individual/2A202603547_PhanTrongHau.md) và [danh mục kết quả](../results/README.md). Hai mươi câu cũ đã được xem trước nên được phân loại lại làm dev; không tính là holdout độc lập.

## Kiểm tra code và phát lại demo

```bash
python3 scripts/check_tests.py
.venv/bin/python scripts/build_nd13_report.py
.venv/bin/python scripts/demo.py --scenario all
```

Demo phát lại trace đã lưu, không gọi model. Test mới có một lỗi protocol trên `nd13-25` và citation sai trang trên `nd13-23`; report giữ nguyên các lỗi này. Unit tests kiểm tra code/mock, không thay thế đánh giá agent thật.

## Cài môi trường và hỏi agent

Chạy lệnh từ thư mục gốc repo. Python >=3.11; lockfile được kiểm tra với CPython 3.14.9 trên Linux. Cần Ollama; khởi động `ollama serve` nếu server chưa chạy. Không cần `.env` hay API key.

```bash
uv venv --python 3.14
uv pip sync --python .venv/bin/python requirements.lock.txt
ollama pull qwen3:4b-instruct
.venv/bin/python scripts/prepare_nd13.py
.venv/bin/python scripts/ask.py "Trong Chương I, dữ liệu cá nhân được chia thành hai nhóm nào?" --config lexical
```

Trace câu hỏi trực tiếp mặc định lưu tại `results/demo/trace.json`; dùng `--output` để lưu tên khác. Có thể chọn `baseline`, `lexical`, `hybrid`, `mmr`, `rerank`. Chỉ dùng `--chapter` khi người dùng nói rõ chương. Không chạy đồng thời hai tiến trình dùng chung Qdrant local path.

## Artifact benchmark

- `benchmark/nd13/dev.json`, `benchmark/nd13/test.json`: cases, gold và absence checks.
- `configs/experiments.json`: cấu hình, retrieval và giả thuyết.
- `results/nd13/v2/dev/<method>/`: trace/review của năm phương pháp.
- `results/nd13/v2/selection.json`: winner và checksum đóng băng.
- `results/nd13/v2/test/{baseline,lexical}/`: test trace/review/metrics sau freeze.
- `results/nd13/validation.json`: metrics được report dùng.

`results/nd13/v2/test` đã chứa trace cuối; không cần chạy lại test để xem report. Re-running `scripts/run_nd13.py --split test` cần model/Ollama và index đã chuẩn bị; runner tiếp tục trace còn thiếu với benchmark/config/code/model hash đã đóng băng. Không thay đổi cấu hình dựa trên test đã xem; đánh giá thay đổi cần test mới.

Mỗi trace ghi model, tool calls, query/filter, ranking/context, citations, token, thời gian, phí dịch vụ và lỗi. Nhãn review có AI hỗ trợ, kèm lý do đối chiếu; học viên cần rà nguồn và xác nhận trước khi nộp.

## Giới hạn nguồn

PDF là bản ký số năm 2023; OCR còn lỗi. BGE-small-en-v1.5 và MiniLM được giữ từ pipeline Day 06 và dùng với tiếng Việt. Không dùng kết quả này để khẳng định quy định hiện hành hoặc tư vấn pháp lý. Alice chỉ còn là artifact benchmark lịch sử.
