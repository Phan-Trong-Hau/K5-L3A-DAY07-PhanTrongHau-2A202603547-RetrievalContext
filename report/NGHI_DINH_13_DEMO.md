# Agentic RAG trên Nghị định 13/2023/NĐ-CP

**Bộ dữ liệu đánh giá hiện tại:** tài liệu tiếng Việt từ Day 06, OCR 39 trang; 88 đoạn, vector BGE-small-en-v1.5 384 chiều; 20 câu hỏi đóng băng trước khi chạy. Nguồn là [bản ký số năm 2023 do Chính phủ công bố](https://chinhphu.vn/default.aspx?docid=207759&pageid=27160). Bài Alice không được dùng cho kết quả trong báo cáo này.

## Kết quả kiểm tra

| Phương pháp | Agent trả lời | Lỗi chạy | Gold trong top-3 truy vấn gốc | Gold trong context cuối | Đã gọi search | Citation nằm trong context |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 6/20 | 0 | 12/20 | 5/20 | 20/20 | 6/20 |
| lexical | 16/20 | 2 | 19/20 | 20/20 | 20/20 | 16/20 |
| hybrid | 15/20 | 0 | 15/20 | 15/20 | 20/20 | 15/20 |
| mmr | 12/20 | 0 | 10/20 | 11/20 | 20/20 | 12/20 |
| rerank | 17/20 | 0 | 16/20 | 17/20 | 20/20 | 17/20 |

**Unit tests: 43/43 pass.** Đây là kiểm tra code với mock/fake provider; không xác nhận chất lượng ngữ nghĩa của model.

Không phải mọi case end-to-end đều đạt. Bằng chứng retrieval, trạng thái `answered`, và tính đúng đắn của câu trả lời được đo riêng. Ví dụ reranker trả lời sai câu `vi03` (nhầm “Bên Kiểm soát dữ liệu cá nhân” thành “Bên Kiểm soát và xử lý dữ liệu cá nhân”); BM25 trả lời `ABSTAIN` cho `vi04` dù đoạn luật có trong context; một số câu bị bỏ sót bởi dense/MMR. Không gọi trạng thái answered là pass nếu chưa kiểm tra đáp án và citation về mặt nghĩa.

## Năm phương pháp

1. **Dense:** cosine trên vector BGE Day 06.
2. **BM25:** lexical matching trên OCR tiếng Việt.
3. **Hybrid:** reciprocal-rank fusion của dense và BM25.
4. **MMR:** chọn đoạn liên quan nhưng giảm trùng lặp trong shortlist dense.
5. **Rerank:** hybrid shortlist, chấm cặp query–document bằng MiniLM cross-encoder.

Cả 20 câu external test đã được chạy qua cả năm phương pháp (100 lượt). Chúng tôi không chọn winner hoặc chỉnh tham số bằng chính tập test này. Không có ND13 dev set trong lần đánh giá này.

## Giới hạn

Embedding và cross-encoder được giữ nguyên từ pipeline Day 06, cả hai có tên model tiếng Anh và được áp dụng lên tiếng Việt; vì thế kết quả không đại diện cho chất lượng tối đa của mô hình đa ngữ. OCR giữ nguyên các lỗi nhận dạng trong nguồn. Nghị định là bản ký số năm 2023, không phải tư vấn pháp lý hay xác nhận quy định hiện hành.

## Tái lập

```bash
.venv/bin/python scripts/prepare_nd13.py
.venv/bin/python scripts/run_nd13.py
python3 scripts/check_tests.py
.venv/bin/python scripts/build_nd13_report.py
```

Protocol đóng băng: `benchmark/nd13/protocol.json`. Chi tiết trace từng phương pháp: `results/nd13/test/<method>/traces.json`. PDF và OCR snapshot được giữ tại `data/nd13/`.
