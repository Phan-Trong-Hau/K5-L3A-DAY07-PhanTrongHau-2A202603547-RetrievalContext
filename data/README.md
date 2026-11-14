# Định dạng và nguồn dữ liệu

## Dataset dùng cho bài nộp

Benchmark hiện tại dùng `nd13/`: PDF ký số Nghị định 13/2023/NĐ-CP, OCR 39 trang, 88 chunks và vectors 384 chiều được chuẩn bị từ Day 06. `source_manifest.json` và `provenance.json` ghi nguồn, quyền, model, dimension và checksum. Đây là snapshot năm 2023; không dùng làm xác nhận pháp lý hiện hành.

Các câu hỏi đang chấm ở `../benchmark/nd13/dev.json` và `../benchmark/nd13/test.json`. Gold gồm nguồn, số trang PDF và evidence quote; câu thiếu evidence có `absence_reason` cùng audit terms. Gold chỉ dùng trong evaluation, không đưa vào prompt hoặc retrieval.

`day6/` giữ lại artifact Alice của benchmark lịch sử và các file ví dụ cho starter; chúng không tạo số liệu cho báo cáo Nghị định 13 hiện tại.

## Schema

Các artifact là JSON UTF-8. Mỗi chunk có `id`, `text`, `source_id`, `source`, `page`, `metadata`; ID phải duy nhất. Mỗi câu có `id`, `split`, `question`, `answerable`; câu trả lời được có `expected_answer` và `gold` gồm `{source_id, page, evidence}`. Câu không trả lời được cần `absence_reason` và cách kiểm tra nguồn. Có thể thêm `filter` chỉ khi suy ra được từ câu hỏi/yêu cầu, không lấy từ gold.

Giữ liên kết đến tài liệu gốc, trang và metadata. Đối chiếu trang/evidence với nguồn; trích nguyên văn OCR không tự đảm bảo đáp án đúng.

Xem thêm [benchmark protocol](../benchmark/nd13/protocol.json), [hướng dẫn chạy](../docs/ND13.md) và [data schema mẫu](../starter/README.md).
