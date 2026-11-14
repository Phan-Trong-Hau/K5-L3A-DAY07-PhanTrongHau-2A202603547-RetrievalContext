# Cách chạy và tái lập

**Bộ đánh giá hiện tại:** [Nghị định 13 tiếng Việt](ND13.md), 20 câu qua năm phương pháp; trace tại `results/nd13/`. Hướng dẫn v2/Alice dưới đây là benchmark lịch sử. Lệnh live `scripts/ask.py` mặc định dùng Nghị định 13.

Chạy mọi lệnh từ thư mục gốc repo. Python >=3.11; bản lock được chạy với CPython
3.14.9 trên Linux. Cần Ollama cài sẵn; nếu server chưa chạy, mở terminal khác với
`ollama serve`. Không cần `.env` hoặc API key.

## Cài môi trường

```bash
uv venv --python 3.14
uv pip sync --python .venv/bin/python requirements.lock.txt
ollama pull qwen3:4b-instruct
python3 -m unittest discover -s tests -v
```

Không có `uv`: tạo virtualenv Python >=3.11 rồi `pip install -r requirements.txt`.
Lần đầu FastEmbed tải model ONNX công khai; cần mạng để tải. Model tải về được kiểm
tra hash tokenizer/ONNX trùng Day 6; không khớp thì dừng, không chuyển sang model giả.
Model sinh khoảng 2.5 GB; GPU 4 GB chạy được với cấu hình hiện tại, có thể fallback
CPU của Ollama nhưng chậm hơn. Không tự tải model 7B hoặc gọi API tính phí.

## Hỏi agent

```bash
.venv/bin/python scripts/ask.py "Trong Chương I, dữ liệu cá nhân được chia thành hai nhóm nào?" --config rerank
.venv/bin/python scripts/ask.py "Kinh phí bảo vệ dữ liệu cá nhân của doanh nghiệp do ai bố trí?" --config lexical
```

Mỗi lần lưu trace tại `results/demo/trace.json`; dùng `--output` để giữ nhiều ví dụ.
Không truyền `--config` thì dùng cấu hình đã chốt trên dev; có thể chọn một trong
`baseline`, `lexical`, `hybrid`, `mmr`, `rerank` để xem riêng từng phương pháp.
`--chapter IX` chỉ khi người dùng yêu cầu chương đó; không lấy chương từ gold.
Không chạy đồng thời hai tiến trình dùng cùng Qdrant local path vì store có khóa.

## Xem bài nộp

- `benchmark/dev.json`, `benchmark/test.json`: câu hỏi, đáp án, evidence/absence audit.
- `configs/experiments.json`: baseline và hai cấu hình thử cải thiện.
- `results/dev/*/traces.json`, `results/test/*/traces.json`: trace thật từng câu.
- `reviews.json`: nhãn đối chiếu câu trả lời, context, citation và lý do.
- `summary.json`, `audit_summary.json`, `comparison.json`: số liệu tổng hợp.
- `results/selection.json`: winner chốt trên dev trước test; hash model/config/code/data.
- Các lần chạy thử tích hợp chỉ lưu cục bộ, không nộp; tóm tắt ở `results/README.md`.

## Tái lập trong thư mục mới

```bash
.venv/bin/python scripts/reproduce.py --output runs/reproduction-01
```

Lệnh tạo bản sao code/config/benchmark/snapshot trong thư mục mới rồi chạy **dev**,
giữ nguyên kết quả đã nộp. Sau khi đọc trace và viết nhãn `reviews.json` cho mỗi
cấu hình, dùng Python của môi trường gốc để chạy các lệnh sau từ thư mục mới:

```bash
python scripts/freeze.py --split dev
python -m src.run --split test
# Đọc toàn bộ baseline + winner test, ghi reviews.json ở mỗi thư mục kết quả.
python scripts/freeze.py --split test
```

`python` ở đoạn này là executable của virtualenv đã kích hoạt bằng `source
<repo-gốc>/.venv/bin/activate`. Không copy nhãn cũ vào kết quả mới một cách máy móc.
Runner lưu sau từng câu và có thể tiếp tục lượt dở bằng lệnh cũ nếu hash không đổi.
Chạy dev trong bản nộp đã freeze sẽ bị từ chối để tránh chỉnh theo test.

Schema nhãn mỗi câu thành công:

```json
{
  "query_id": "q01",
  "reviewer": "Tên người/AI đọc đối chiếu",
  "answer_grade": 2,
  "context_grade": 2,
  "citation_support": [true],
  "reason": "Giải thích đối chiếu nguồn, điều kiện, câu trả lời và từng citation."
}
```

Với câu thiếu evidence, bỏ hai trường grade, thêm `abstention_correct: true/false`.
Lượt lỗi giữ nguyên trace lỗi, không thêm nhãn thành công. Script không tự chấm
ngữ nghĩa; người chấm phải đọc nguồn. Bài nộp có nhãn AI hỗ trợ, cần người học rà lại.

## Tái xuất từ Day 6 (không cần khi chỉ chấm bài)

Trong một bản sao repo chưa freeze, có thể dùng:

```bash
.venv/bin/python scripts/import_day6.py --day6 ../K5-L3A-DAY06-PhanTrongHau-2A202603547-DataIngestion
.venv/bin/python scripts/prepare_benchmark.py
```

Script chỉ mở bản sao tạm của `.qdrant` Day 6, xuất collection C và copy văn bản
công khai; không sửa repo Day 6. Không chạy sau khi đã freeze vì thay snapshot/nhãn.
