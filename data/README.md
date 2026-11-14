# Định dạng dữ liệu

## Snapshot bài nộp

`day6/` chứa 192 chunk và vector thật từ collection C Day 6 của Phan Trọng Hậu.
Corpus Alice có 82 trang logic theo quy ước Day 6. ID, URL, page và metadata giữ nguyên.
`provenance.json` ghi nguồn, quyền sử dụng, model/dimension và checksum;
`embedding.json` ghi revision/hash tokenizer và ONNX. Giấy phép Gutenberg giữ trong
`alice.txt`. Toàn bộ dữ liệu này công khai, không chứa secret/API key.

Benchmark thật nằm trong `benchmark/dev.json` và `benchmark/test.json`; các file
`example_*.json` bên dưới chỉ dành cho starter/test, không dùng tính kết quả bài nộp.

## Schema gốc

Các file `example_*.json` chỉ minh họa định dạng, không đủ để nộp bài. Dữ liệu thật là JSON array UTF-8; nếu dùng định dạng khác, ghi cách chuyển trong README.

- **Chunk:** `id`, `text`, `source_id`, `source`, `page`, `metadata`. ID phải duy nhất; giữ phiên bản hoặc ngày nếu có.
- **Câu có đáp án:** `id`, `split` (`dev` hoặc `test`), `question`, `expected_answer`, `gold`: danh sách `{source_id, page, evidence}`. Với schema mẫu, mỗi evidence phải nằm trọn trong một chunk đúng nguồn và trang; các phần tử `gold` là evidence thay thế. Với câu multi-hop cần nhiều đoạn, bạn có thể mở rộng schema, ghi rõ nhóm evidence bắt buộc và cách chấm. Có thể thêm `filter` do người dùng cung cấp trước.
- **Câu thiếu evidence:** `id`, `split`, `question`, `answerable: false`, `expected_behavior: "search_and_abstain"`, `absence_reason`. Xem `agent_cases_example.json`.

Không đưa `gold` hoặc nhãn đáp án vào model và retrieval tool. Ghi nguồn dữ liệu và quyền sử dụng. Cách chuyển một số định dạng Day 6: [starter/README.md](../starter/README.md).
