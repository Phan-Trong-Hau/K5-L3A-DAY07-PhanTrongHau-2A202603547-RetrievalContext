# Kết quả thực nghiệm

Benchmark hiện tại ở `nd13/v2/`: dev 22 câu × năm phương pháp; test mới 7 câu, chạy baseline và BM25 đã chọn trên dev. Report HTML/Markdown ở `../report/NGHI_DINH_13_DEMO.*`; JSON metrics ở `nd13/validation.json`.

- `nd13/v2/dev/`: traces/reviews của năm phương pháp.
- `nd13/v2/selection.json`: phương pháp được chọn cùng hash dữ liệu, code, cấu hình và model.
- `nd13/v2/test/`: traces/reviews test sau freeze, baseline và cấu hình được chọn.
- `nd13/external_v1/`: giữ nguyên 20 trace đã chạy/xem ở lượt trước; chúng được tái phân loại là dev, không phải holdout độc lập.
- `nd13/code_tests.json`: lần chạy kiểm tra code mới nhất.

Trace lưu output Qwen local, tool calls, ranking/context, usage, thời gian và lỗi. Nhãn đánh giá thủ công có hỗ trợ AI và kèm lý do; người học cần xác nhận. `hit@3`, evidence context, đáp án và citation support là các chỉ số khác nhau.

Test mới có một lỗi protocol của BM25 ở câu `nd13-25`: đoạn luật được tìm thấy, nhưng model bỏ qua retrieval rồi kết thúc bằng lỗi. Lỗi được tính điểm 0; các trace không bị sửa sau đánh giá.
