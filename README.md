# Day 7 — Agentic RAG

**Bài cá nhân · Python 3.11+ · tiếp nối Day 6**

## Bản triển khai của Phan Trọng Hậu — 2A202603547

Đã có pipeline local trong `src/`: **dense Qdrant Day 6, BM25, hybrid RRF,
dense MMR và hybrid cross-encoder rerank**. Bài đánh giá hiện tại dùng tài liệu
tiếng Việt [Nghị định 13/2023/NĐ-CP](report/NGHI_DINH_13_DEMO.html): benchmark
dev 22 câu × 5 phương pháp và test mới 7 câu (baseline + BM25 được chọn từ dev).
Các kết quả Alice trước đó được giữ riêng làm lịch sử, không dùng trong lần đánh
giá Nghị định 13. Xem [quy trình benchmark tiếng Việt](docs/ND13.md),
[thiết kế](docs/IMPLEMENTATION.md) và [hướng dẫn chạy](docs/RUNNING.md).

Để demo kết quả Nghị định 13, mở [báo cáo HTML](report/NGHI_DINH_13_DEMO.html)
bằng trình duyệt. Nó chạy offline và có thể in/lưu PDF. Trace thật nằm trong
`results/nd13/v2/test/<method>/traces.json`.
Để phát lại ví dụ thật đã lưu mà không gọi model mới, chạy
`python3 scripts/demo.py --scenario all`.

Phần bonus đang có corpus text theo trang cho [Việt Nam 2035](data/bonus/vietnam2035/README.md), trích xuất từ 573/584 trang PDF bằng Poppler. Chạy `python3 scripts/index_vietnam2035.py /path/to/vietnam2035_vi.pdf` để dựng lại index, sau đó `python3 scripts/search_vietnam2035.py "câu hỏi"` để tìm BM25. [Báo cáo HTML bonus](report/BONUS_TRIAL.html) ghi kết quả benchmark, đối chiếu từng câu và giới hạn hiện tại. Bonus chưa đạt ngưỡng 90%; [trace thăm dò](results/bonus/pilot/README.md) không phải điểm test bonus.

Chạy kiểm tra offline bằng `python3 -m unittest discover -s tests -v`.
Chạy agent thật sau khi cài dependency và bật Ollama:

```bash
uv venv --python 3.14
uv pip sync --python .venv/bin/python requirements.lock.txt
ollama pull qwen3:4b-instruct
.venv/bin/python scripts/ask.py "Trong Chương I, dữ liệu cá nhân được chia thành hai nhóm nào?"
```

Snapshot OCR/vector Nghị định 13 từ Day 6 nằm trong `data/nd13/`; Alice vẫn ở
`data/day6/` để tái lập benchmark cũ. Kết quả Nghị định 13 nằm ở `results/nd13/`.
Chạy lại bằng [hướng dẫn Nghị định 13](docs/ND13.md).

## Đề bài gốc

Dùng embedding và vector store từ Day 6 để xây một agent biết tìm bằng chứng, trả lời có nguồn và nhận biết khi không đủ thông tin. Bạn tự chọn kiến trúc, số tool và cách tổ chức retrieval.

> **Tùy chọn:** [Gợi ý dùng AI để lập trình](AGENT_SETUP.md) giúp bạn làm lab; phần này không bắt buộc và không tính điểm.

## Bài cần làm

![Agent tìm tài liệu trong kho Day 6 và trả lời có nguồn](assets/retrieval-pipeline.svg)

1. Kết nối dữ liệu, embedding và vector store Day 6.
2. Xây agent dùng model thật và ít nhất một khả năng truy xuất dữ liệu. Agent có thể dùng nhiều tool và nhiều lượt gọi.
3. Thử **ít nhất 3 phương pháp retrieval khác nhau**, trong đó có dense retrieval dùng vector store Day 6. Tự chọn các phương pháp còn lại; xem [gợi ý](GUIDE.md#2-thử-các-phương-pháp-retrieval).
4. Thử nhiều cấu hình, benchmark, phân tích lỗi và chọn cấu hình tốt trên **dev**; sau đó đánh giá trên **test**.

Benchmark tối thiểu có **24 câu**: dev gồm 15 câu có đáp án và 2 câu thiếu bằng chứng; test gồm 5 câu có đáp án và 2 câu thiếu bằng chứng. Xem [benchmark](BENCHMARK.md) và [rubric](RUBRIC.md).

## Thử thách nâng cao · +15 điểm

Index một tài liệu thực tế từ **100 trang** có bảng, ảnh và biểu đồ; xây agent truy xuất và trả lời các câu hỏi về nội dung đó. Hoàn thành [thử thách nâng cao](ADVANCED.md) và đạt **ít nhất 90% benchmark test** để nhận 15 điểm bonus. Phần cơ bản tối đa 85 điểm; toàn bài tối đa 100 điểm.

## Bắt đầu

1. Đọc [hướng dẫn](GUIDE.md), [rubric](RUBRIC.md) và [quy tắc](RULES.md).
2. Tạo repo cá nhân theo [cách nộp bài](SUBMISSION.md), chuẩn bị đầu ra Day 6 và model hỗ trợ tool calling.
3. Dùng hoặc thay thế [starter](starter/README.md); bạn cần kết nối model và vector store thật.
4. Chạy `python -m unittest discover -s tests -v`. Test mock chỉ kiểm tra code, không phải benchmark agent thật.

![Các bước thử nghiệm trên dev và đánh giá trên test](assets/experiment-loop.svg)

Nộp code, cách chạy, cấu hình, benchmark, trace và [báo cáo cá nhân đã điền](report/individual/2A202603547_PhanTrongHau.md). Thời gian ở [checkpoints](CHECKPOINTS.md) là gợi ý, có thể điều chỉnh theo lớp và phạm vi thử nghiệm.
