# Demo: Agentic RAG trên Nghị định 13/2023/NĐ-CP

## Mục tiêu

So sánh năm phương pháp retrieval trên tài liệu tiếng Việt của Day 06, chọn cấu hình chỉ bằng dev, rồi đánh giá một lần trên test mới. Bản PDF ký số năm 2023 được giữ nguyên cùng OCR, chunks và vector Day 06. Không dùng bài Alice cho benchmark này.

## Thiết kế benchmark

- Dev: 22 câu, 20 có đáp án và 2 câu cố ý không có bằng chứng; dùng so sánh 5 phương pháp.
- Test đóng băng: 7 câu mới, 5 có đáp án và 2 thiếu bằng chứng; chỉ chạy baseline và phương pháp được chọn trên dev.
- Hai mươi câu đã chạy và xem trước ở phiên trước được lưu dưới `results/nd13/external_v1/` và dùng lại làm dev; chúng không được tính là holdout độc lập.
- Quy tắc chọn: điểm answer grade trung bình trên dev (0–2; lỗi chạy tính 0), sau đó lần lượt xét abstention đúng, evidence trong context, latency.
- BM25 tiếng Việt (`lexical`) được chọn trên dev. Model: Qwen 3 4B local; corpus và code được hash/freeze trước test.

## Cấu hình và giả thuyết đã đo

| Cấu hình | Retrieval | top-k | candidates | Context budget | Tìm tối đa | Giả thuyết |
|---|---|---:|---:|---:|---:|---|
| baseline | dense | 3 | — | 1200 ký tự | 1 | Day 6 dense with small context; same v2 controller as all other configurations. |
| lexical | bm25 | 5 | — | 4800 ký tự | 2 | Exact lexical matching with larger context. |
| hybrid | hybrid | 5 | 20 | 4800 ký tự | 2 | Fuse dense and BM25 ranks with RRF. |
| mmr | mmr | 5 | 20 | 4800 ký tự | 2 | Dense candidates selected by 0.75 relevance minus 0.25 redundancy to improve context diversity. |
| rerank | rerank | 5 | 20 | 4800 ký tự | 2 | Hybrid shortlist re-scored by a real MiniLM cross-encoder query-document model. |

BM25 thử khớp từ vựng chính xác với context lớn hơn, kỳ vọng giữ tên/điều kiện OCR bị dense bỏ sót. Hybrid thử hợp nhất thứ hạng dense và BM25 bằng RRF, kỳ vọng lấy được evidence bị một nhánh bỏ qua. Đây là so sánh giữa các cấu hình gói, chưa tách ablation tác động riêng của context budget.

## Kết quả test mới

| Cấu hình | Hit@1 | Evidence Hit@3 | Context evidence | Answer 0/1/2, TB /2 | Context 0/1/2 | Citation hỗ trợ | Trả lời có citation | Tool use* | Phân bố lượt search | Abstain đúng | Từ chối nhầm | Lỗi | Median s | Tổng s | Token tổng | Phí dịch vụ |
|---|---:|---:|---:|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 1/5 (20%) | 2/5 (40%) | 1/5 (20%) | 4/0/1 (0.40/2) | 4/0/1 | 1/1 (100%) | 1/1 (100%) | 6/6 (100%) | 1 câu: 0 lượt, 6 câu: 1 lượt | 2/2 (100%) | 3/5 (60%) | 1 | 7.3 | 51.4 | 8828 | $0.00 |
| lexical | 4/5 (80%) | 5/5 (100%) | 4/5 (80%) | 1/1/3 (1.40/2) | 1/0/4 | 3/4 (75%) | 4/4 (100%) | 6/6 (100%) | 1 câu: 0 lượt, 6 câu: 1 lượt | 2/2 (100%) | 0/5 (0%) | 1 | 18.0 | 169.7 | 15170 | $0.00 |

BM25 trả lời đúng về nội dung ở 4/5 câu có đáp án, nhưng chỉ 3/4 citation được hỗ trợ đúng đoạn; ở `nd13-23`, câu trả lời nêu đúng điều kiện nhưng citation trỏ sang trang 15 thay vì đoạn luật ở trang 11, nên được chấm answer 1/2. BM25 từ chối đúng 2/2 câu không có bằng chứng. Câu `nd13-25` là lỗi giao thức: model bỏ qua retrieval bắt buộc và kết thúc bằng lỗi. Ranking truy vấn gốc được tính độc lập sau lượt chạy có đoạn bằng chứng trang 21, nhưng đoạn đó không nằm trong context cuối gửi model; không tính ranking offline thành retrieval thành công của agent. Điểm câu này là 0. Baseline trả lời đúng 1/5 câu, từ chối đúng 2/2 câu thiếu evidence, và có một lỗi giao thức.

### Chấm từng câu

| Case | Method | Trạng thái | Answer / 2 | Context / 2 | Abstention | Câu trả lời / lỗi | Nhận xét đối chiếu |
|---|---|---|---:|---:|---|---|---|
| nd13-21 | baseline | abstain | 0 | 0 | — | ABSTAIN: Không tìm thấy thông tin về thời gian bên kiểm soát phải thực hiện yêu cầu khi chủ thể phản đối xử lý dữ liệu để ngăn tiết lộ hoặc dùng cho quảng cáo, tiếp thị trong Chương II của Nghị định số 13/2023/NĐ-CP. Dữ liệu hiện có không cung cấp thời gian cụ | Abstained on an answerable case; no gold passage in context. |
| nd13-22 | baseline | abstain | 0 | 0 | — | ABSTAIN: Không có thông tin trong văn bản về những bên nào phải ngừng xử lý dữ liệu của chủ thể sau khi đã thông báo hậu quả và nhận yêu cầu rút lại đồng ý. Các đoạn trích chỉ nêu rõ việc thông báo hậu quả khi nhận yêu cầu rút lại đồng ý, nhưng không đề cập đế | Abstained on an answerable case; no gold passage in context. |
| nd13-23 | baseline | abstain | 0 | 0 | — | ABSTAIN: Không tìm thấy thông tin trong văn bản về trường hợp bên kiểm soát có thể không cung cấp dữ liệu vì việc cung cấp có thể ảnh hưởng đến người khác. Các đoạn trích hiện có không đề cập đến điều kiện này. | Gold was in original top-3 but omitted from final context; abstention is incorrect. |
| nd13-24 | baseline | answered | 2 | 2 | — | [1d0358ad25ac5f8a0c558624a7d5e37d8044ee809f2ffe51c2afc3f8ea19e13b] Trong trường hợp không thể thực hiện yêu cầu chỉnh sửa dữ liệu cá nhân, phải thông báo cho chủ thể dữ liệu sau 72 giờ kể từ khi nhận được yêu cầu chỉnh sửa dữ liệu cá nhân của chủ thể dữ liệu. | Correct 72-hour answer; cited passage on page 13 supports it. |
| nd13-25 | baseline | error | 0 | 0 | — | ValueError: Model skipped mandatory retrieval after protocol repair | Runtime protocol error; no final evidence context. |
| nd13-test-missing-03 | baseline | abstain | — | — | đúng | ABSTAIN: Không tìm thấy thông tin về số điện thoại đường dây nóng của Cục An ninh mạng và phòng, chống tội phạm sử dụng công nghệ cao trong văn bản. | Không có yêu cầu trong tài liệu; câu trả lời đúng là từ chối kèm diễn giải thiếu bằng chứng. |
| nd13-test-missing-04 | baseline | abstain | — | — | đúng | ABSTAIN: Không có thông tin trong Nghị định số 13/2023/NĐ-CP về mức ngân sách hằng năm được ấn định chính xác cho hoạt động bảo vệ dữ liệu cá nhân của doanh từng doanh nghiệp. Các đoạn trích không cung cấp số tiền cụ thể nào liên quan đến ngân sách này. | Không có yêu cầu trong tài liệu; câu trả lời đúng là từ chối kèm diễn giải thiếu bằng chứng. |
| nd13-21 | lexical | answered | 2 | 2 | — | Bên kiểm soát phải thực hiện yêu cầu của chủ thể dữ liệu trong 72 giờ sau khi nhận được yêu cầu, trừ trường hợp luật có quy định khác [51d959173d4170c537b6084a90aed280f9f23686012e7fb35df30bdd427ff480]. | Correct 72-hour limit and legal exception; cited page 8 passage supports answer. |
| nd13-22 | lexical | answered | 2 | 2 | — | Sau khi đã thông báo hậu quả và nhận yêu cầu rút lại sự đồng ý, Bên Kiểm soát dữ liệu cá nhân, Bên Xử lý dữ liệu, Bên Kiểm soát và xử lý dữ liệu, Bên thứ ba phải ngừng và yêu cầu các tổ chức, cá nhân có liên quan ngừng xử lý dữ liệu của chủ thể dữ liệu đã rút  | Names all four parties and the requirement to request related parties stop; cited passage supports answer. |
| nd13-23 | lexical | answered | 1 | 2 | — | Bên kiểm soát có thể không cung cấp dữ liệu cá nhân trong trường hợp việc cung cấp có thể ảnh hưởng tới sự an toàn, sức khỏe thể chất hoặc tinh thần của người khác [fbda52817cf9dc390fcfacee45492fa572d492b51579d556749c614201aac65b]. | Answer states the right condition and gold is present in context, but its citation resolves to page 15 and does not support the claim on page 11. |
| nd13-24 | lexical | answered | 2 | 2 | — | Theo Điều 15, khoản 2, điểm b của Nghị định số 13/2023/NĐ-CP, nếu không thể thực hiện yêu cầu chỉnh sửa dữ liệu cá nhân thì Bên Kiểm soát dữ liệu cá nhân, Bên Kiểm soát và xử lý dữ liệu cá nhân phải thông báo tới chủ thể dữ liệu sau 72 giờ kể từ khi nhận được  | Correct 72-hour deadline and triggering request; cited page 13 passage supports answer. |
| nd13-25 | lexical | error | 0 | 0 | — | ValueError: Model skipped mandatory retrieval after protocol repair | Independent evaluation of the original query ranking found the page 21 evidence, but the agent tool loop skipped mandatory retrieval and ended in protocol error; final context is empty. |
| nd13-test-missing-03 | lexical | abstain | — | — | đúng | ABSTAIN: Không có thông tin về số điện thoại đường dây nóng của Cục An ninh mạng và phòng, chống tội phạm sử dụng công nghệ cao trong các đoạn trích đã cung cấp. | Không có yêu cầu trong tài liệu; câu trả lời đúng là từ chối kèm diễn giải thiếu bằng chứng. |
| nd13-test-missing-04 | lexical | abstain | — | — | đúng | ABSTAIN: Nghị định 13/2023/NĐ-CP không quy định rõ ràng về mức ngân sách hằng năm cụ thể (đồng) mà doanh nghiệp phải chi cho hoạt động bảo vệ dữ liệu cá nhân. Chỉ nêu rằng kinh phí bảo vệ dữ liệu cá nhân của tổ chức, doanh nghiệp do các tổ chức, doanh nghiệp t | Không có yêu cầu trong tài liệu; câu trả lời đúng là từ chối kèm diễn giải thiếu bằng chứng. |

## So sánh dev dùng để chọn

| Method | Hit@1 | Evidence Hit@3 | Context evidence | Answer 0/1/2, TB /2 | Context 0/1/2 | Citation hỗ trợ | Trả lời có citation | Tool use* | Phân bố lượt search | Abstain đúng | Từ chối nhầm | Lỗi | Median s | Tổng s | Token tổng | Phí dịch vụ |
|---|---:|---:|---:|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 5/20 (25%) | 12/20 (60%) | 5/20 (25%) | 15/0/5 (0.50/2) | 7/8/5 | 5/6 (83%) | 6/6 (100%) | 22/22 (100%) | 22 câu: 1 lượt | 2/2 (100%) | 14/20 (70%) | 0 | 7.7 | 177.2 | 28134 | $0.00 |
| lexical | 12/20 (60%) | 19/20 (95%) | 20/20 (100%) | 6/2/12 (1.30/2) | 0/0/20 | 14/18 (78%) | 16/16 (100%) | 20/20 (100%) | 22 câu: 1 lượt | 2/2 (100%) | 2/20 (10%) | 2 | 16.6 | 394.2 | 58437 | $0.00 |
| hybrid | 13/20 (65%) | 15/20 (75%) | 15/20 (75%) | 10/0/10 (1.00/2) | 0/5/15 | 10/15 (67%) | 15/15 (100%) | 22/22 (100%) | 22 câu: 1 lượt | 2/2 (100%) | 5/20 (25%) | 0 | 20.9 | 827.7 | 56580 | $0.00 |
| mmr | 5/20 (25%) | 10/20 (50%) | 11/20 (55%) | 10/1/9 (0.95/2) | 0/9/11 | 11/14 (79%) | 12/12 (100%) | 22/22 (100%) | 22 câu: 1 lượt | 2/2 (100%) | 8/20 (40%) | 0 | 16.3 | 453.2 | 52275 | $0.00 |
| rerank | 13/20 (65%) | 16/20 (80%) | 17/20 (85%) | 6/2/12 (1.30/2) | 0/3/17 | 13/19 (68%) | 17/17 (100%) | 22/22 (100%) | 22 câu: 1 lượt | 2/2 (100%) | 3/20 (15%) | 0 | 27.9 | 815.8 | 52498 | $0.00 |

## Hai lỗi dev đã đối chiếu

- `vi03` (định nghĩa Bên Kiểm soát): dense, hybrid, MMR và rerank đều trả lời nhầm vai trò “Bên Kiểm soát và xử lý dữ liệu cá nhân”; BM25 tìm thấy gold trong top-3/context nhưng lỗi citation-format repair. Đoạn luật ở trang 3 phân biệt hai thuật ngữ sát nhau. Đây là lỗi hiểu/giữ tên pháp lý và format citation; thêm retriever không tự giải quyết, cần output validation và đọc sát định nghĩa.
- `vi08` (rút lại đồng ý): BM25 tìm đủ evidence nhưng lỗi `Invalid citations after format repair`; hybrid và rerank trên cùng dev trả lời grade 2 với citation được hỗ trợ, còn baseline từ chối do không đưa evidence vào context. So sánh trace cho thấy retrieval đủ không bảo đảm agent kết thúc hợp lệ; lựa chọn BM25 vẫn dựa trên điểm trung bình toàn dev, không sửa theo test.

Đây là phân tích chéo các phương pháp trên cùng dev, không phải ablation sau khi sửa lỗi. Không dùng test để điều chỉnh.

* Tool use dùng mẫu số các case hoàn thành; lỗi được báo riêng. False abstention và answer grade tính trên toàn bộ câu có đáp án; runtime error được chấm 0. Citation support yêu cầu ID nằm trong context và nội dung citation hỗ trợ claim. Latency gồm toàn bộ agent run, token là tổng prompt + completion, phí dịch vụ local bằng 0 USD (điện/phần cứng chưa tính).

## Năm phương pháp

1. Dense cosine trên vector BGE Day 06.
2. BM25 lexical trên OCR tiếng Việt.
3. Hybrid dense + BM25 bằng reciprocal-rank fusion.
4. MMR giảm các đoạn trùng lặp trong shortlist dense.
5. Rerank shortlist hybrid bằng MiniLM cross-encoder.

## Kiểm tra và giới hạn

**Unit tests: 52/52 pass.** Đây là kiểm tra code bằng mock/fake provider, không đại diện chất lượng trả lời thực tế. Test end-to-end không pass hết: BM25 có một lỗi protocol trên `nd13-25`; kết quả được giữ nguyên trong report.

Dev/test là benchmark nội bộ nhỏ, phần review ngữ nghĩa có hỗ trợ AI và cần người học xác nhận. OCR có lỗi nhận dạng. BGE-small-en-v1.5 và MiniLM là model có tên tiếng Anh được giữ từ pipeline Day 06 khi xử lý tiếng Việt. Nguồn là văn bản năm 2023, không xác nhận quy định hiện hành và không phải tư vấn pháp lý.

## Artifact để demo

- Protocol: `benchmark/nd13/protocol.json`
- Câu hỏi: `benchmark/nd13/dev.json`, `benchmark/nd13/test.json`
- Chọn cấu hình và hash: `results/nd13/v2/selection.json`
- Trace test: `results/nd13/v2/test/<method>/traces.json`
- Report dữ liệu: `results/nd13/validation.json`
- PDF nguồn: `data/nd13/13nd.signed.pdf`

Chạy lại code tests: `python3 scripts/check_tests.py`. Chạy viewer trace: `.venv/bin/python scripts/demo.py --scenario all`.

## Trạng thái thử thách bonus

Đã lập corpus và thử nghiệm riêng trên báo cáo tiếng Việt *Việt Nam 2035*. Bộ test độc lập V3 đạt **25/30 (83,3%)**, thấp hơn ngưỡng 27/30 theo `ADVANCED.md`; do đó chưa đạt bonus. Dev V4 đạt 16/18, thấp hơn V3 (17/18), nên V4 không được chọn và không chạy trên test. Việc kiểm chứng hình ảnh mới bao phủ tám hình, chưa bao phủ toàn bộ hình có ích của tài liệu.

Xem [report bonus HTML](BONUS_TRIAL.html), [corpus và giới hạn xử lý hình](../data/bonus/vietnam2035/README.md), [benchmark/test review](../results/bonus/test_v3_fresh/reviews.json), và [metrics](../results/bonus/test_v3_fresh/metrics.json). Kết quả chi tiết và lỗi theo từng câu được giữ nguyên; không tính bonus là hoàn thành.
