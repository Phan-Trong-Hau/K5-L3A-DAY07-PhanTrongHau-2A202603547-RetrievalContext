# Thử nghiệm thăm dò, chưa phải benchmark bonus

- `asean.json`: lần chạy đầu, agent truy xuất đúng trang PDF 77 nhưng sau khi
  sửa định dạng trích dẫn chỉ xuất mã nguồn, không có nội dung; không đạt.
- `asean_after_fix.json`: chạy lại sau khi sửa chuẩn hóa trích dẫn. Agent trả
  lời 4,8% và trích dẫn trang PDF 77. Đã đối chiếu Bảng 1.1 trong PDF gốc:
  hàng ASEAN, cột 2016–2035, là 4,8%; kết quả này đạt cho câu thăm dò.
- `hinh_2_11.json`: thử với mô tả Hình 2.11 đã kiểm tra thủ công. Agent trả
  lời than cao nhất, hàng dệt thấp nhất trong nhóm tỷ trọng sản lượng. Đối chiếu
  các thanh màu xanh trên trang PDF 118 xác nhận thứ tự này; kết quả đạt cho
  câu thăm dò. Hiện chỉ bốn hình đã có mô tả kiểm chứng, chưa phải toàn bộ
  đồ họa của tài liệu.
- `vision_118.jsonl`: mô hình `qwen2.5vl:3b` thử đọc cùng trang ở độ phân giải
  960 pixel, giới hạn 160 token. Kết quả mất khoảng 48 giây, bị cắt theo giới
  hạn token và chép sai một số nhãn, ví dụ “Cao su và đá” thay cho “Cao su và
  chất dẻo”. Không coi đầu ra này là bằng chứng đã xác minh.
- `clip_search_118.json`: truy vấn tiếng Việt tìm biểu đồ tỷ trọng sản lượng
  doanh nghiệp nhà nước trên chỉ mục CLIP đủ 584 trang không đưa trang PDF 118
  vào 10 vùng đầu. Đây là lỗi truy xuất; việc có đủ vector không đảm bảo tìm
  được nội dung đúng.
- `clip_search_118_english.json`: với truy vấn mô tả bằng tiếng Anh tương đương,
  vùng trên bên phải của trang 118 xếp thứ 10/10. Kết quả này cho thấy ảnh hưởng
  của câu truy vấn nhưng chưa chứng minh độ chính xác đủ dùng cho tiếng Việt.
- `visual_agent_118.json`: agent thử tìm bằng BM25 + CLIP và nhờ vision model
  đọc trang. Kết quả **không đạt**: agent dẫn nhầm trang PDF 117 và thêm tỷ lệ
  90% không được Hình 2.11 ghi bằng nhãn số; hình thực tế ở trang 118. Vision
  model trả kết quả bị cắt và tự nêu các tỷ lệ không được kiểm chứng. Tổng thời
  gian agent khoảng 108 giây. Đây là bằng chứng rõ rằng pipeline đọc hình tự
  động hiện không đáng tin, không phải kết quả benchmark chính thức.
- Các lần chạy là thử nghiệm phát triển; không dùng làm test độc lập và không
  thể suy ra điểm bonus. Trace ghi context, các lượt gọi model/tool, token và
  thời gian; chi phí dịch vụ Ollama local là 0 USD, chưa tính điện/phần cứng.

Tài liệu gốc: [Việt Nam 2035](https://documents.worldbank.org/curated/en/462881491821948950/pdf/103435-v2-VIETNAMESE-PUBLIC-PUBDATE-11-30-2016.pdf).
