# Giới hạn xử lý hình, bảng và biểu đồ

- CLIP đã tạo vector cho toàn bộ 584 trang, gồm ảnh toàn trang và bốn góc
  (2.920 vùng). Đây là độ phủ đầu vào, không chứng minh vector lưu được chữ
  nhỏ, hình mảnh hay các giá trị biểu đồ. Không nộp bản PDF hay các ảnh crop;
  dùng PDF gốc và script để tái tạo vector.
- Bộ dò nhận được 152 nhãn hình/bảng và `pdfimages` liệt kê 304 đối tượng ảnh
  hoặc mask trên 107 trang. Không thể cộng hai số này thành tổng số hình: nhiều
  biểu đồ là vector, nhiều bitmap là mask/trang trí, và bộ dò nhãn có thể bỏ sót.
- Tám hình ở các trang PDF 118, 281, 285, 287, 309, 360, 362 và 394 đã được
  đối chiếu thủ công và mô tả trong `visual_verified_v2.jsonl`. Các hình còn lại
  chưa có mô tả ngữ nghĩa được đối chiếu đầy đủ; số lượng chính xác chưa xác
  định. Ảnh hưởng: câu hỏi yêu cầu đọc màu, số liệu hoặc quan hệ trên các hình
  đó có thể không được trả lời hoặc bị trả lời sai.
- Trong thử nghiệm trang 118, truy vấn CLIP tiếng Việt không tìm đúng trang
  trong top 10; mô hình vision đọc nhầm nhãn và thêm số không được chứng minh;
  agent kết hợp còn dẫn nhầm trang. Chi tiết và trace ở `results/bonus/pilot/`.
  Những đầu ra này là dữ liệu thử nghiệm, không được xem là bằng chứng đúng.
- Mười một trang PDF có ít chữ đã được nhìn trực tiếp: 10 trang trắng và một
  trang chỉ có tiêu đề. Chi tiết ở `skipped_pages_audit.json`.

Vì còn các giới hạn trên, điểm số của bất kỳ bộ câu hỏi nào cũng không tự nó
chứng minh rằng pipeline đã xử lý chính xác toàn bộ nội dung trực quan của báo
cáo. Tiếp tục kiểm tra bản gốc trước khi coi phần nâng cao là hoàn thành.
