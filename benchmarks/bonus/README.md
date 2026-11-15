# Benchmark dự thảo: Việt Nam 2035

Hai tệp `dev_draft.json` và `test_draft.json` được soạn cùng lúc trước khi thử
các cấu hình dev. Dev có 15 câu có đáp án và 3 câu thiếu bằng chứng; test có
24 câu có đáp án (6 bảng, 5 ảnh, 5 biểu đồ, 4 multi-hop, 4 text) và 6 câu
thiếu bằng chứng. Chúng là **dự thảo**, chưa phải điểm benchmark chính thức:
các câu thiếu bằng chứng vẫn cần kiểm tra toàn văn, dữ liệu trực quan trên
toàn tài liệu chưa được xử lý đầy đủ, và cần rà soát độc lập độ đa dạng câu hỏi.
Sau khi đã bắt đầu chạy dev, hai câu ảnh test dự thảo được chỉnh để bỏ sự
trùng lặp với dev và yêu cầu đọc chú giải hình; test vẫn chưa được chạy. Vì
thay đổi này xảy ra sau khi bắt đầu thử nghiệm, không coi bộ dự thảo này là
bằng chứng của một thiết kế đã đóng băng trước thử nghiệm.

Mỗi câu ghi trang PDF vật lý và vị trí kiểm chứng. Khi chạy,
`scripts/run_bonus.py` chỉ đưa câu hỏi vào agent; đáp án chuẩn và trang evidence
không được đưa vào agent. Ví dụ chạy thử dev:

```sh
.venv/bin/python scripts/run_bonus.py --questions benchmarks/bonus/dev_draft.json --output results/bonus/dev_bm25_k3 --top-k 3 --visual-index data/bonus/vietnam2035/visual_verified.jsonl
.venv/bin/python scripts/run_bonus.py --questions benchmarks/bonus/dev_draft.json --output results/bonus/dev_caption_k3 --method bm25_caption --top-k 3 --visual-index data/bonus/vietnam2035/visual_verified.jsonl
```

Mỗi lần chạy tạo manifest và trace cho từng câu; có thể chạy lại cùng lệnh để
tiếp tục các câu chưa chạy. `scripts/audit_bonus.py` tạo mẫu và tổng hợp nhãn
kiểm tra thủ công; nó không tự chấm đúng sai. Không chọn cấu hình dựa trên test.

Phép thử truy xuất riêng trên 15 câu dev có đáp án được lưu tại
`results/bonus/dev_retrieval_probe_v2.json`: BM25 tìm đủ trang ở 11/15 câu,
BM25 ưu tiên nhãn bảng/hình ở 15/15 câu. Số này chỉ kiểm tra trang nằm trong
top-3, không kiểm tra câu trả lời, trích dẫn hay khả năng từ chối và không thể
thay thế điểm benchmark. Các mô tả trực quan mới chỉ được đối chiếu 4 hình.

Lượt `dev_bm25_k3` dùng prompt từ chối ban đầu và đạt 13/18 theo đối chiếu
thủ công trong `reviews.json`; ba câu multi-hop không đạt. Lượt
`dev_caption_v2` dùng cả cách ưu tiên nhãn và prompt từ chối ngắn hơn, vì vậy
so sánh hai lượt đánh giá toàn bộ cấu hình, không chứng minh riêng tác động
của từng thay đổi. Lượt sau đạt 17/18; câu không đạt từ chối đúng nhưng nhầm
năm của một số liệu được nêu thêm. Các lượt này vẫn là thăm dò trên bộ dự thảo.

Lượt test dự thảo với cấu hình thứ hai đạt **22/30 (73,3%)**, không có lỗi hệ
thống. Theo nhóm: bảng 5/6, ảnh 4/5, biểu đồ 4/5, multi-hop 2/4, text 4/4,
thiếu bằng chứng 3/6. Đối chiếu từng câu nằm trong
`results/bonus/test_caption_draft/reviews.json`; trace và thống kê thời gian,
token trong cùng thư mục. Tổng thời gian agent 1.206,9 giây, chi phí dịch vụ
Ollama 0 USD, chưa tính điện và khấu hao. Đây không đạt 90% và không đủ điều
kiện nhận bonus. Nếu dùng kết quả này để chỉnh cấu hình, phải tạo test mới
độc lập trước khi báo điểm mới.

Sau khi phân tích test dự thảo, đã bổ sung policy v3 và soạn
`test_fresh_v3.json` với câu hỏi mới; không dùng lại test cũ để báo điểm v3.
Tệp test mới và `visual_verified_v2.jsonl` được ghi trước khi bắt đầu lượt dev
v3 mở rộng. Tệp này chưa được chạy, chấm hoặc xác nhận đạt chuẩn; cần tiếp tục
kiểm tra tính độc lập, bằng chứng thiếu và nội dung gốc trước khi báo điểm.
