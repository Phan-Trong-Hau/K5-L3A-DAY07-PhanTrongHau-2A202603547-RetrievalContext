# Báo cáo Day 7 — Agentic RAG

**Phan Trọng Hậu · 2A202603547 · L3A**

Cấu hình được chọn trên dev: **lexical**. Test có **5/5 câu có đáp án đạt grounded grade 2**. Trong 2 câu thiếu evidence, có **2 lỗi giao thức**; model từ chối trước khi gọi retrieval. Không tính các lỗi này là abstention đúng. Đã giữ nguyên code/config sau freeze và báo cả kết quả không đạt.

## Dữ liệu và benchmark

- Corpus: *Alice’s Adventures in Wonderland*, Lewis Carroll; [Project Gutenberg #11](https://www.gutenberg.org/ebooks/11). Bản tải gốc và giấy phép giữ trong `data/day6/alice.txt`.
- Tiếp nối collection **C** Day 6: **192 chunk, 82 đơn vị trang logic**, giữ nguyên ID/text/nguồn/page/metadata và vector. Đây không phải PDF 82 trang. Không làm bonus tài liệu từ 100 trang.
- Dense: Qdrant local, exact cosine, **BAAI/bge-small-en-v1.5**, **384 chiều**, FastEmbed 0.9.1. Query dùng `query_embed` tương thích Day 6; không re-embed tài liệu. Snapshot ONNX/tokenizer được đối chiếu SHA-256.
- Agent thật: **qwen3:4b-instruct**, Q4_K_M, Ollama local; temperature 0, seed 7, cửa sổ 8192 token, tối đa 384 token sinh/lượt. Máy đo: NVIDIA GTX 1650 4 GB, CPython 3.14.9. Model digest: `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
- Dev: 15 câu có đáp án tái dùng từ Day 6 + 2 câu thiếu evidence mới. Test: **5 câu có đáp án mới + 2 câu thiếu evidence mới**, không dùng lại test Day 6. Tổng cộng **24 câu**. Câu hỏi tiếng Anh phù hợp corpus/embedding tiếng Anh.
- Gold gồm nguồn, trang logic, trích đoạn nguyên văn; mỗi câu có một đoạn evidence đủ trong một chunk. Câu thiếu evidence được kiểm tra bằng quét toàn corpus và đọc cảnh liên quan; xem `benchmark/absence_audit.json`.
- Gold/expected answer chỉ vào evaluation sau generation; agent chỉ nhận question và filter người dùng nêu rõ. Chương III/VI/IX/VIII/XI chỉ được lọc khi câu hỏi đã ghi chương, áp dụng giống nhau cho cả ba phương pháp.
- Nhãn do **Codex hỗ trợ đọc đối chiếu trace và nguồn**, có reviewer/lý do trong `reviews.json`; chưa phải xác nhận thủ công của học viên. Người học cần rà lại trước nộp. Không dùng mock hoặc tự gán expected answer làm output model.

## Retrieval, context và thử nghiệm

Baseline dense giữ cơ chế cosine Day 6, context 1.200 ký tự và một lượt search. Cải thiện 1 dùng BM25 (`k1=1.5`, `b=0.75`), context 4.800 ký tự và tối đa hai search để giữ thêm đoạn và thử lại query. Cải thiện 2 dùng hybrid RRF (`k=60`, 20 candidate mỗi nhánh), cùng budget/lượt với lexical để kết hợp semantic và từ khóa. Hai cấu hình cải thiện đồng thời là phương pháp retrieval thứ hai và thứ ba. Đây là so sánh theo gói cấu hình, chưa phải ablation từng thành phần.

| Cấu hình | Method / top-k / budget ký tự / search | Split | Hit@1 | Evidence Hit@3 | Context Evidence Rate | Median giây/câu | Tổng giây agent | Phí dịch vụ |
|---|---|---|---|---|---|---|---|---|
| baseline | dense / 3 / 1200 / 1 | dev | 9/15 (60.0%) | 14/15 (93.3%) | 9/15 (60.0%) | 8.87 | 159.04 | 0 USD |
| lexical (chọn) | bm25 / 5 / 4800 / 2 | dev | 13/15 (86.7%) | 14/15 (93.3%) | 14/15 (93.3%) | 19.99 | 295.63 | 0 USD |
| hybrid | hybrid / 5 / 4800 / 2 | dev | 12/15 (80.0%) | 15/15 (100.0%) | 15/15 (100.0%) | 17.78 | 317.73 | 0 USD |
| baseline | dense / 3 / 1200 / 1 | test | 4/5 (80.0%) | 5/5 (100.0%) | 3/5 (60.0%) | 8.52 | 47.02 | 0 USD |
| lexical (chọn) | bm25 / 5 / 4800 / 2 | test | 2/5 (40.0%) | 5/5 (100.0%) | 5/5 (100.0%) | 21.12 | 119.02 | 0 USD |

Hit@1/3 đo ranking **query gốc** tại cùng cutoff 1/3. Query viết lại và kết quả từng tool được lưu riêng. Context Evidence Rate đo context cuối thật sự gửi model; không suy từ top-3 query gốc. Budget gồm cả header ID/nguồn/trang. Context giữ chunk nguyên vẹn, loại trùng và hợp nhất rank qua lượt tìm; chunk không vừa bị bỏ. Phí API 0 USD do chạy local, **không** bao gồm điện/phần cứng. Median/tổng trên là thời gian vòng agent, không gồm nạp index và lượt kiểm tra ranking gốc sau generation.

Thứ tự chạy dev: baseline → lexical → hybrid, dùng lại model/query-embedding cache trong một tiến trình. Latency phản ánh điều kiện cache hỗn hợp; không phải phép so sánh cold-start cô lập. Context lớn hơn có thể tăng prompt cost/latency; giới hạn hai lượt search không có nghĩa model luôn dùng hết.

## Hai lỗi dev và kết quả trước/sau

### q04: How were the words on the small cake written?

- Baseline: **abstain**; context evidence **False**. ABSTAIN: The context does not contain any information about how the words on the small cake were written.
- Cấu hình chọn `lexical`: **answered**; context evidence **True**. The words on the small cake were beautifully marked in currants. [2a30fa3ded62…]
- Nguyên nhân: dense query gốc có hit, nhưng query model thêm tên truyện làm ranking chuyển sang đoạn kể chuyện ở bàn trà. Đây là lỗi query transformation; chỉ tăng budget không đảm bảo khôi phục bằng chứng đã rớt khỏi candidate. BM25/hybrid được thử để giữ các từ khóa cake/words.

### q06: What prize did the Dodo present to Alice?

- Baseline: **answered**; context evidence **False**. The Dodo did not present a specific prize to Alice; instead, Alice handed out a box of comfits as prizes to the group, with one piece for each person. [5bd76e4d944d…]
- Cấu hình chọn `lexical`: **answered**; context evidence **True**. The Dodo did not present a prize to Alice. Instead, Alice handed out a box of comfits as prizes to the group. [5bd76e4d944d…]
- Nguyên nhân: tool dense tìm thấy p15 (Alice phát comfits) trước p16 (Dodo tặng thimble). Context 1.200 ký tự giữ p15 rồi không đủ chỗ cho p16. Model suy diễn sai từ việc thiếu đoạn kế tiếp. Hai cấu hình context lớn hơn được đo lại để kiểm tra khả năng giữ evidence đúng.

### Lỗi còn lại và giới hạn

Dev `q13` cho thấy retrieval/context có thể chứa đủ danh sách bốn nhánh Arithmetic nhưng model từ chối vì cho rằng đó không phải toán học thật. Cần phân biệt nội dung hư cấu trong truyện với kiến thức đời thực. Đây là lỗi reasoning/grounding, không thể kết luận chỉ từ citation ID hợp lệ. Các nhãn và kết quả không cải thiện vẫn giữ nguyên trong bảng và trace.

Lexical `q14` còn minh họa lỗi citation: model nói đúng old conger-eel/once a week nhưng cite `aa49e3…` ở p82 (chị Alice tưởng tượng em lớn lên), trong khi evidence nằm ở p62. ID có trong context nhưng không hỗ trợ đáp án. Theo protocol đòi được citation hỗ trợ, answer grade là 0 và citation support là false. Giữ nguyên ID SHA-256 Day 6 giúp truy vết. ID dài hoặc cách model chọn nguồn là các giả thuyết cho lỗi này; chưa có ablation để xác định nguyên nhân.

## Chọn trên dev, đánh giá test sau freeze

Điểm dev dùng để chọn (lỗi câu có đáp án tính 0): **baseline: 1.067/2**; **lexical: 1.400/2**; **hybrid: 1.333/2**. Mean chất lượng trên lượt thành công ở bảng dưới có thể cao hơn vì loại riêng lỗi; không dùng mean đó để ưu ái cấu hình có lỗi.

Chọn **lexical**, chốt lúc **2026-11-14T04:41:40.438775+00:00**. Tiêu chí công bố trước: tối đa grounded-answer mean dev (lỗi tính 0 khi chọn), rồi tỷ lệ abstention đúng, context evidence, median thời gian thấp hơn và tên cấu hình. File `results/selection.json` lưu tiêu chí, toàn bộ dev comparison và hash code/config/model/corpus/dev/test/reviews. Sau freeze chỉ chạy baseline và winner trên cùng test; không thay code/config theo test.

## Agent và đánh giá câu trả lời

Model dùng native `search_documents`, có thể viết lại query và tìm tiếp; kết thúc bằng `submit_answer` hoặc final text. Phải tìm trước khi kết thúc. Từ chối được model phát ra rõ `ABSTAIN:`; các tham chiếu đoạn liên quan trong raw refusal được bỏ khỏi citation đầu ra, raw message vẫn giữ trong trace. Lỗi provider/schema/citation không hợp lệ có status `error`, không thay bằng từ chối giả. Nội dung tài liệu chỉ là dữ liệu. Citation được kiểm tra membership và đọc đối chiếu ngữ nghĩa trong nhãn.

| Cấu hình / split | Tool use | Phân bố lượt search | Grounded 0/1/2; mean /2 | Context 0/1/2 | Citation hỗ trợ | Câu trả lời có citation | Abstention đúng | Từ chối nhầm | Lỗi |
|---|---|---|---|---|---|---|---|---|---|
| baseline / dev | 17/17 (100.0%) | 1 lượt: 17 câu | 7/0/8; 1.067/2 | 3/3/9 | 9/10 (90.0%) | 10/10 (100.0%) | 2/2 (100.0%) | 5/15 (33.3%) | 0 |
| hybrid / dev | 16/16 (100.0%) | 1 lượt: 17 câu | 4/0/10; 1.429/2 | 0/0/14 | 11/13 (84.6%) | 12/12 (100.0%) | 2/2 (100.0%) | 2/14 (14.3%) | 1 |
| lexical / dev | 17/17 (100.0%) | 1 lượt: 17 câu | 4/1/10; 1.400/2 | 0/1/14 | 11/13 (84.6%) | 13/13 (100.0%) | 2/2 (100.0%) | 2/15 (13.3%) | 0 |
| baseline / test | 5/5 (100.0%) | 0 lượt: 2 câu, 1 lượt: 5 câu | 2/0/3; 1.200/2 | 1/1/3 | 3/4 (75.0%) | 4/4 (100.0%) | 0/0 (N/A) | 1/5 (20.0%) | 2 |
| lexical / test | 5/5 (100.0%) | 0 lượt: 2 câu, 1 lượt: 5 câu | 0/0/5; 2.000/2 | 0/0/5 | 6/6 (100.0%) | 5/5 (100.0%) | 0/0 (N/A) | 0/5 (0.0%) | 2 |

Grounded/context 0/1/2 lần lượt là sai hoặc thiếu / một phần / đủ. Citation hỗ trợ được chấm theo từng citation, không đồng nhất với đáp án đầy đủ. Lượt lỗi báo riêng; quality mean trên câu có đáp án thành công; tiêu chí chọn phạt lỗi bằng 0.

Trong thực nghiệm này, mọi câu đã gọi tool đều chỉ dùng một lượt search dù lexical/hybrid cho phép hai lượt. Vì vậy chưa có bằng chứng về lợi ích của multi-round; cải thiện đo được đi cùng thay đổi retriever/context, không thể quy cho việc tăng giới hạn số lượt.

Hai câu thiếu evidence ở test làm model phát `ABSTAIN` ngay từ lượt đầu, trước bất kỳ tool call nào, nên runner ghi error thay vì công nhận search-and-abstain. Vì cả hai lượt đều lỗi, abstention quality có mẫu số 0 (N/A), không phải đạt 100%. Tool use 5/5 trên lượt thành công cũng không che đi 2/7 lượt lỗi. Đây là giới hạn điều phối đã bộc lộ trên holdout; muốn cải thiện cần tạo test mới và đo lại, không sửa rồi báo lại cùng test như độc lập.

## Đọc toàn bộ test: baseline và cấu hình chọn

Các ID citation được viết ngắn trong bảng để dễ đọc; ID đầy đủ, context, tool call và nhãn nằm ở liên kết trace. Đã đối chiếu cả 5 câu có đáp án và 2 câu thiếu evidence cho mỗi cấu hình.

### baseline

[Trace](../../results/test/baseline/traces.json) · [Nhãn và lý do](../../results/test/baseline/reviews.json)

| Query | Search | Kết quả | Context / Answer | Nhận xét đối chiếu |
|---|---|---|---|---|
| t01 | 1 | answered: The White Rabbit took out a pair of white kid gloves and a large fan from its waistcoat-pocket. [48834728b6b0…] | 0 / 0 | Sai vật thể và tình huống: evidence p1 là watch lấy từ waistcoat-pocket; context/citation p8 chỉ nói Rabbit cầm gloves và fan, không nói lấy chúng từ túi áo. Citation không hỗ trợ mệnh đề của câu trả lời. |
| t02 | 1 | answered: The White Rabbit called Alice "Mary Ann" when mistaking her for his housemaid [39ac42315a7d…]. | 2 / 2 | P18 Rabbit gọi Why, Mary Ann và nhầm Alice là housemaid; citation chứa cả tên và tình huống hỏi. |
| t03 | 1 | answered: The Caterpillar took the hookah out of its mouth before addressing Alice [930898f8ac40…]. | 2 / 2 | P26 mở đầu ghi Caterpillar took the hookah out of its mouth trước addressed her; citation đúng vật và thứ tự. |
| t04 | 1 | abstain: ABSTAIN: The provided passage does not explain why the gardeners were painting the white roses red. It describes the scene and the gardeners' interactions but does not provide a reason for the action of painting the roses. | 1 / 0 | False abstention. Context p48 mới có cảnh sơn hoa trắng thành đỏ và chuyện tulip-roots/onions, chưa có đoạn Two giải thích trồng nhầm cây trắng và sợ bị chém đầu. Source đúng nhưng điều kiện/nguyên nhân thiếu. |
| t05 | 1 | answered: The White Rabbit held a trumpet in one hand and a scroll of parchment in the other. [03205044b1ea…] | 2 / 2 | P70 ghi Rabbit near King with trumpet in one hand and scroll of parchment in the other. Citation hỗ trợ đủ hai đồ vật và mỗi tay. |
| t-missing-1 | 0 | error: ValueError: Expected exactly one native tool call per turn | abstention=None | Lỗi giao thức: model phát ABSTAIN ngay lượt đầu mà không gọi retrieval; validator giữ status error. Không tính thành từ chối đúng dù biết câu thiếu evidence. Raw output và lỗi lưu trong events; không sửa code theo test. |
| t-missing-2 | 0 | error: ValueError: Expected exactly one native tool call per turn | abstention=None | Lỗi giao thức: model phát ABSTAIN ngay lượt đầu mà không gọi retrieval; validator giữ status error. Không tính thành từ chối đúng dù biết câu thiếu evidence. Raw output và lỗi lưu trong events; không sửa code theo test. |

### lexical

[Trace](../../results/test/lexical/traces.json) · [Nhãn và lý do](../../results/test/lexical/reviews.json)

| Query | Search | Kết quả | Context / Answer | Nhận xét đối chiếu |
|---|---|---|---|---|
| t01 | 1 | answered: The White Rabbit took a watch out of its waistcoat-pocket [ab539a3db10e…]. | 2 / 2 | P1 ghi Rabbit took a watch out of its waistcoat-pocket; model trả watch, giữ đúng vật và tình huống, citation ab539a… hỗ trợ trực tiếp. |
| t02 | 1 | answered: The White Rabbit called Alice "Mary Ann" when mistaking her for his housemaid [39ac42315a7d…]. | 2 / 2 | P18 Rabbit gọi Why, Mary Ann và nhầm Alice là housemaid; citation chứa cả tên và tình huống hỏi. |
| t03 | 1 | answered: The Caterpillar took the hookah out of its mouth before addressing Alice. [930898f8ac40…] | 2 / 2 | P26 mở đầu ghi Caterpillar took the hookah out of its mouth trước addressed her; citation đúng vật và thứ tự. |
| t04 | 1 | answered: The gardeners were painting the white roses red because the rose-tree was supposed to be red, and they had mistakenly planted a white one. If the Queen discovered the mistake, they would all be beheaded. Therefore, they were painting the roses red to hide the error before the Queen arrived. [b070f72b180b…][133a7dd5f74e…] | 2 / 2 | P48: b070f7… hỗ trợ cảnh gardeners sơn hoa trắng thành đỏ; 133a7d… có lời Two về trồng nhầm cây trắng thay đỏ và sợ Queen chém đầu. Hai citation cùng hỗ trợ đủ cảnh/động cơ/điều kiện; đáp án đầy đủ. |
| t05 | 1 | answered: The White Rabbit held a trumpet in one hand and a scroll of parchment in the other near the King at the trial [03205044b1ea…]. | 2 / 2 | P70 ghi Rabbit near King with trumpet in one hand and scroll of parchment in the other. Citation hỗ trợ đủ hai đồ vật và mỗi tay. |
| t-missing-1 | 0 | error: ValueError: Expected exactly one native tool call per turn | abstention=None | Lỗi giao thức: model phát ABSTAIN ngay lượt đầu mà không gọi retrieval; validator giữ status error. Không tính thành từ chối đúng dù biết câu thiếu evidence. Raw output và lỗi lưu trong events; không sửa code theo test. |
| t-missing-2 | 0 | error: ValueError: Expected exactly one native tool call per turn | abstention=None | Lỗi giao thức: model phát ABSTAIN ngay lượt đầu mà không gọi retrieval; validator giữ status error. Không tính thành từ chối đúng dù biết câu thiếu evidence. Raw output và lỗi lưu trong events; không sửa code theo test. |

## Thời gian, token và tái lập

| Cấu hình / split | Prompt token | Completion token | Tổng thời gian agent (s) |
|---|---|---|---|
| baseline / dev | 23789 | 2124 | 159.04 |
| hybrid / dev | 44951 | 2230 | 317.73 |
| lexical / dev | 45233 | 2024 | 295.63 |
| baseline / test | 8089 | 667 | 47.02 |
| lexical / test | 14488 | 736 | 119.02 |

Token là tổng qua các lượt model, bao gồm context/prompt lặp; không quy đổi ra tiền API. Thông tin phiên bản và digest mỗi cấu hình nằm ở `environment.json`/`manifest.json`. Các lượt chạy thử tích hợp trước benchmark chỉ lưu cục bộ, không nằm trong bài nộp và không gộp vào số liệu; tóm tắt ở `results/README.md`.

```bash
python3 -m unittest discover -s tests -v
uv venv --python 3.14
uv pip sync --python .venv/bin/python requirements.lock.txt
ollama pull qwen3:4b-instruct
.venv/bin/python scripts/ask.py "What prize did the Dodo present to Alice?"
.venv/bin/python scripts/reproduce.py --output runs/reproduction-01
```

Xem [hướng dẫn đầy đủ](../../docs/RUNNING.md), [thiết kế](../../docs/IMPLEMENTATION.md), [protocol](../../benchmark/protocol.json), [dev comparison](../../results/dev/comparison.json), [test comparison](../../results/test/comparison.json), [freeze](../../results/selection.json).

Giới hạn: bộ test nhỏ; nhãn AI hỗ trợ cần người học xác nhận; exact evidence có thể bỏ sót cách diễn đạt/nguồn thay thế; chưa đánh giá tiếng Việt, multi-hop, reranker hoặc đa phương thức. Không tuyên bố đạt bonus 15 điểm. Không suy rộng điểm số của bộ này thành độ chính xác trên mọi tài liệu.
