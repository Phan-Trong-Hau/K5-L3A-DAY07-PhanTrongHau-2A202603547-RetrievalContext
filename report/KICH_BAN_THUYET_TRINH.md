# Kịch bản demo và thuyết trình Agentic RAG

**Người trình bày:** Phan Trọng Hậu · 2A202603547 · L3A  
**Thời lượng gợi ý:** 8–10 phút, gồm khoảng 2 phút demo.  
**Tài liệu mở chính:** [Báo cáo demo](BAO_CAO_DEMO.md).

## 1. Chuẩn bị trước khi trình bày

1. Mở terminal tại root repo, tăng cỡ chữ để người xem đọc được.
2. Chạy thử `python3 scripts/demo.py --scenario improvement`; màn hình phải ghi rõ phát lại trace đã lưu.
3. Mở `report/BAO_CAO_DEMO.html` bằng trình duyệt và mở sẵn `results/selection.json`.
4. Nếu demo live, chuẩn bị `.venv`, Ollama và model trước; dành khoảng 20–30 giây cho mỗi câu, có thể lâu hơn tùy máy.
5. Không chạy lại toàn bộ benchmark trong lúc thuyết trình. Giữ trace đã lưu làm phương án dự phòng; không giới thiệu replay là suy luận live.

## 2. Lời dẫn theo từng phần

### Phút 0 đến 1 giới thiệu bài toán

**Mở:** mục 1 và 2 của báo cáo demo.

> Em trình bày bài Day 7 về Agentic RAG, tiếp nối dữ liệu của Day 6. Mục tiêu là xây một agent biết tìm bằng chứng trong tài liệu, trả lời kèm nguồn và nhận biết khi thiếu thông tin. Em triển khai ba cách retrieval và đánh giá riêng từng tầng để xác định nguyên nhân khi hệ thống trả lời sai.
>
> Kết quả chính là cấu hình BM25 trả lời đầy đủ năm câu test có đáp án. Tuy nhiên, hai câu thiếu bằng chứng vẫn gặp lỗi điều phối. Vì vậy, em sẽ trình bày cả phần cải thiện và giới hạn còn lại.

**Điểm cần nhấn:** 5/5 chỉ áp dụng cho nhóm có đáp án; không nói hệ thống đạt 100% toàn test.

### Phút 1 đến 2 dữ liệu và kiến trúc

**Mở:** bảng thiết lập và sơ đồ ở mục 2–3.

> Em dùng lại 192 chunk từ collection C Day 6, cùng ID, metadata và vector thật. Corpus là Alice’s Adventures in Wonderland, gồm 82 đơn vị trang logic, không phải 82 trang PDF. Dense retrieval dùng BGE 384 chiều và Qdrant local. Model điều phối là Qwen 4B chạy qua Ollama.
>
> Khi có câu hỏi, model gọi search_documents. Tool lấy các đoạn liên quan; hệ thống loại trùng, chọn context trong budget và giữ nguồn, trang, ID. Model đọc context rồi trả lời hoặc từ chối. Đáp án chuẩn chỉ dùng sau khi sinh kết quả để đánh giá, không được đưa vào agent.

**Nếu được hỏi vai trò agent:** model thật tạo query và gọi tool; đây không phải một hàm lấy top-k rồi trả expected answer. Hệ thống có khả năng tìm tiếp, nhưng trace trong thực nghiệm này chỉ ghi nhận một lượt tìm ở mỗi câu đã gọi tool.

### Phút 2 đến 3 ba phương pháp và cách đánh giá

**Mở:** bảng cấu hình ở mục 4 và bảng dev ở mục 5.

> Dense tìm theo độ gần embedding. BM25 tìm theo từ khóa và thống kê xuất hiện từ. Hybrid dùng RRF để kết hợp thứ hạng hai nhánh, tránh cộng hai loại score khác thang đo.
>
> Baseline có context 1.200 ký tự. Hai cấu hình cải thiện dùng context 4.800 ký tự. Đây là so sánh theo gói cấu hình, nên em chưa kết luận riêng phần tăng budget hay đổi retriever đóng góp bao nhiêu.
>
> Em đo Hit@1, Evidence Hit@3 cho query gốc, rồi đo evidence trong context cuối và chất lượng câu trả lời. Citation còn được đọc đối chiếu nội dung, vì ID hợp lệ chưa chắc hỗ trợ câu trả lời.

### Phút 3 đến 4 vì sao chọn BM25

**Mở:** bảng dev và `results/selection.json`.

> Trên dev, baseline có điểm chọn 1,067 trên 2; lexical đạt 1,400; hybrid đạt 1,333. Lỗi trên câu có đáp án được tính bằng 0 khi chọn. Hybrid tìm đủ evidence cho 15 trên 15 câu, nhưng vẫn có lỗi trả lời và citation, nên không phải cấu hình được chọn theo tiêu chí đã đặt.
>
> Em chốt lexical trước khi chạy test. Đánh đổi là median thời gian tăng từ khoảng 9 lên khoảng 20 giây mỗi câu. Phí dịch vụ bằng 0 vì chạy local, nhưng số này không tính điện và phần cứng.

**Chuyển ý:** “Sau đây em mở trace để thấy sự khác biệt xảy ra ở đâu.”

### Phút 4 đến 6 demo cải thiện và từ chối

**Chạy lần lượt:**

```bash
python3 scripts/demo.py --scenario improvement
python3 scripts/demo.py --scenario abstention
```

> Đây là phát lại trace thật đã lưu, không phải một lượt suy luận trực tiếp mới. Với câu hỏi về chữ trên chiếc bánh, baseline bị lệch query và không có evidence đúng trong context. Lexical trả lời currants và dẫn nguồn ở trang logic 6.
>
> Với câu hỏi ngày sinh chính xác của Alice, trace dev cho thấy agent có tìm kiếm rồi từ chối. Em đã rà corpus để xác nhận không có ngày sinh, thay vì chỉ dựa vào việc top-k không tìm thấy. Ví dụ này thuộc dev, không thay cho đánh giá holdout.

**Chỉ trên màn hình:** query tool thực tế, số lượt search, trạng thái context, câu trả lời, trang citation và lý do chấm.

### Phút 6 đến 7 demo lỗi và kết quả test

```bash
python3 scripts/demo.py --scenario failure
python3 scripts/demo.py --scenario holdout-error
```

> Với câu Dodo tặng Alice món gì, context đã chứa đáp án thimble nhưng model vẫn trả lời sai và cite đoạn phát comfits. Đây là lỗi ở tầng trả lời và grounding, dù retrieval đã mang bằng chứng về.
>
> Trên test, lexical trả lời đủ năm câu có đáp án, nhưng hai câu thiếu evidence bị lỗi: model từ chối ngay mà không tìm kiếm. Runner không tính đó là search-and-abstain thành công. Em giữ nguyên code sau freeze và ghi rõ lỗi này, không sửa rồi báo lại cùng test như một đánh giá độc lập.

**Tránh nói:** “Agent đã biết từ chối hoàn toàn chính xác.” Kết quả holdout chưa hỗ trợ kết luận đó.

### Phút 7 đến 8 kết luận

**Mở:** bảng test và phần kết luận.

> Bài làm cho thấy cần kiểm tra cả retrieval, context và câu trả lời có nguồn. BM25 với context lớn hơn là lựa chọn tốt nhất trên dev trong ba cấu hình đã thử, và giải quyết được năm câu test có đáp án. Hệ thống vẫn cần cải thiện việc tuân thủ tool và chọn nguồn khi trả lời.
>
> Hướng tiếp theo là kiểm soát yêu cầu tìm trước khi từ chối chắc hơn, đo riêng từng thay đổi và đánh giá trên test mới. Bộ benchmark hiện tại còn nhỏ, nhãn có AI hỗ trợ nên em cần rà lại nguồn trước khi nộp. Em chưa thực hiện phần bonus đa phương thức từ 100 trang.

## 3. Nếu chỉ có năm phút

| Thời lượng | Nội dung giữ lại |
|---|---|
| 0–1 phút | Mục tiêu, corpus, sơ đồ hoạt động |
| 1–2 phút | Ba phương pháp và lý do chọn lexical |
| 2–4 phút | Replay improvement, abstention và holdout-error |
| 4–5 phút | Bảng test, giới hạn và hướng tiếp theo |

Không cần đọc hết cấu hình model hay toàn bộ bảng token. Giữ số liệu và giải thích lỗi ở đúng tầng.

## 4. Câu hỏi phản biện và cách trả lời

**Tại sao hybrid có retrieval tốt nhất nhưng không được chọn?**  
Tiêu chí chính là grounded answer dev, lỗi tính 0. Hybrid có context đủ 15/15 nhưng còn lỗi model/citation; điểm chọn 1,333 thấp hơn lexical 1,400.

**BM25 tốt hơn dense trong mọi trường hợp không?**  
Không có kết luận đó. Kết quả chỉ áp dụng corpus và benchmark này, với các gói cấu hình context khác nhau. Cần ablation và benchmark rộng hơn để so riêng retriever.

**Vì sao test lexical Hit@1 chỉ 2/5 mà trả lời đúng 5/5?**  
Agent đọc nhiều đoạn. Evidence Hit@3 và context evidence đều đạt 5/5; evidence không cần đứng ở vị trí đầu tiên để được đưa vào câu trả lời.

**Số liệu 5/5 có nghĩa hệ thống đạt 100% không?**  
Chỉ là năm câu có đáp án đạt grade 2 theo nhãn AI hỗ trợ. Toàn test có bảy câu, trong đó hai câu thiếu bằng chứng lỗi giao thức. Không thể gọi toàn bộ test đạt 100%.

**Model đã nói ABSTAIN, sao vẫn tính lỗi?**  
Yêu cầu là tìm bằng chứng rồi mới quyết định. Model chưa gọi tool thì không có căn cứ để nói đã kiểm tra corpus. Runner giữ lỗi để không biến việc bỏ qua retrieval thành một kết quả tốt giả.

**Citation đúng ID có bảo đảm đáp án đúng không?**  
Không. Dev q14 có ID hợp lệ nhưng trỏ sang đoạn không hỗ trợ người dạy Drawling. Cần đọc nội dung nguồn và chấm từng citation.

**Có đưa đáp án chuẩn vào model không?**  
Không. Agent chỉ nhận question, filter rõ ràng và context retrieved. Gold dùng để đánh giá sau generation. Dev và test nằm ở file riêng; test chạy sau khi chốt cấu hình và kiểm tra checksum.

**Tại sao không sửa luôn hai lỗi test rồi chạy lại?**  
Nếu dùng lỗi test để điều chỉnh thì test đó đã tham gia phát triển. Cần holdout mới để đánh giá độc lập; báo cáo hiện tại giữ kết quả của phiên bản đã chốt.

**Agent có thật sự tìm nhiều lượt chưa?**  
Code hỗ trợ và có giới hạn lượt, nhưng trong trace thực nghiệm các câu đã gọi tool đều chỉ tìm một lần. Chưa có kết quả chứng minh lợi ích multi-round.

**Ai chấm nhãn và chi phí là bao nhiêu?**  
Nhãn có Codex hỗ trợ đọc đối chiếu, chưa phải xác nhận độc lập của người học. Phí dịch vụ model/embedding là 0 USD do chạy local; chưa tính điện và phần cứng.

**Bài có làm bonus 100 trang không?**  
Chưa. 82 trang ở đây là đơn vị logic từ Day 6, không phải tài liệu 100 trang có bảng, ảnh và biểu đồ như yêu cầu bonus.

## 5. Các số liệu cần nhớ

- **192 chunk · 384 chiều · 24 câu benchmark.**
- **17 dev · 7 test**, trong mỗi split có 2 câu thiếu evidence.
- **Ba phương pháp:** dense, BM25, hybrid RRF.
- **Chọn lexical:** điểm dev 1,400/2, context đủ 14/15.
- **Test lexical:** 5/5 câu có đáp án đạt grade 2, citation hỗ trợ 6/6; 2 câu thiếu evidence lỗi giao thức.
- **30 kiểm thử code đã đạt** trong lần kiểm tra bài nộp; không đồng nghĩa 30 câu benchmark agent đạt.

Nếu quên số liệu, mở bảng trong báo cáo; không ước lượng bằng trí nhớ khi đang trình bày.
