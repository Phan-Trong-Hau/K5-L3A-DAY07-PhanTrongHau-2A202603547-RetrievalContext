# Danh mục báo cáo Day 7

Các file dưới đây là các phiên bản Markdown/HTML cùng nội dung. Mở HTML để trình chiếu; Markdown thuận tiện xem diff và tái tạo.

| Báo cáo | Nội dung |
|---|---|
| [Báo cáo demo Nghị định 13 (HTML)](NGHI_DINH_13_DEMO.html) · [Markdown](NGHI_DINH_13_DEMO.md) | Kết quả Day 6 trên tài liệu tiếng Việt, benchmark dev/test, so sánh năm phương pháp, trace và phân tích lỗi. |
| [Báo cáo demo tổng hợp (HTML)](BAO_CAO_DEMO.html) · [Markdown](BAO_CAO_DEMO.md) | Bản tổng hợp để demo; cùng số liệu với báo cáo Nghị định 13. |
| [Báo cáo cá nhân (HTML)](individual/2A202603547_PhanTrongHau.html) · [Markdown](individual/2A202603547_PhanTrongHau.md) | Báo cáo nộp theo yêu cầu `SUBMISSION.md`, gồm phần cơ bản và trạng thái bonus. |
| [Kịch bản thuyết trình (HTML)](KICH_BAN_THUYET_TRINH.html) · [Markdown](KICH_BAN_THUYET_TRINH.md) | Lời dẫn demo 8–10 phút và câu trả lời cho câu hỏi thường gặp. |
| [Report bonus Việt Nam 2035 (HTML)](BONUS_TRIAL.html) | Nguồn 584 trang, phương pháp, benchmark, chấm từng câu, thời gian, chi phí và giới hạn. |

## Trạng thái

Phần cơ bản dùng Nghị định 13/2023/NĐ-CP và dữ liệu Day 06; BM25 được chọn bằng dev. Test mới gồm 7 câu; có một lỗi runtime và một citation không hỗ trợ đúng claim, nên report không tuyên bố toàn bộ test pass. Lần chạy offline ngày 15/11/2026 có 52/52 unit test pass.

Phần bonus đã được thử trên *Việt Nam 2035*, nhưng chưa đạt yêu cầu: test độc lập V3 là 25/30 (83,3%), dưới ngưỡng 27/30; V4 không được chọn vì dev thấp hơn. Bao phủ hình ảnh chưa đầy đủ. Xem report bonus để biết chi tiết; không coi bonus là hoàn thành.
