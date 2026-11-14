# Day 7 — Agentic RAG

**Bài cá nhân · Python 3.11+ · tiếp nối Day 6**

## Bản triển khai của Phan Trọng Hậu — 2A202603547

Đã có pipeline local trong `src/`: **dense Qdrant Day 6, BM25 và hybrid RRF**,
agent Qwen gọi tool qua Ollama, benchmark 17 dev / 7 test và kiểm tra checksum khi
chốt cấu hình. Xem [thiết kế](docs/IMPLEMENTATION.md), [hướng dẫn chạy](docs/RUNNING.md)
và [báo cáo cá nhân](report/individual/2A202603547_PhanTrongHau.md).

Để demo và thuyết trình, mở [báo cáo HTML](report/BAO_CAO_DEMO.html) cùng
[kịch bản nói 8–10 phút và hỏi đáp](report/KICH_BAN_THUYET_TRINH.html) bằng trình duyệt.
HTML chạy offline, có mục lục, chế độ tập trung và nút in/lưu PDF.
Sửa bản Markdown rồi chạy `python3 scripts/build_html_reports.py` để cập nhật HTML.
Chạy `python3 scripts/demo.py --scenario all` để xem lại trace thật đã lưu;
đây là phát lại kết quả, không phải một lượt chạy model mới.

Chạy kiểm tra offline bằng `python3 -m unittest discover -s tests -v`.
Chạy agent thật sau khi cài dependency và bật Ollama:

```bash
uv venv --python 3.14
uv pip sync --python .venv/bin/python requirements.lock.txt
ollama pull qwen3:4b-instruct
.venv/bin/python scripts/ask.py "What prize did the Dodo present to Alice?"
```

Snapshot dữ liệu/vector Day 6 đã kèm trong `data/day6/`; không cần chạy lại Day 6
hoặc cung cấp API key. Kết quả thực nghiệm và nhãn nằm trong `results/`.

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

Nộp code, cách chạy, cấu hình, benchmark, trace và [báo cáo](report/individual/MSSV_HoTen.md). Thời gian ở [checkpoints](CHECKPOINTS.md) là gợi ý, có thể điều chỉnh theo lớp và phạm vi thử nghiệm.
