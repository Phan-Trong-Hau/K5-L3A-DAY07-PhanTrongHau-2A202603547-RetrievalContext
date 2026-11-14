# Code

Bản triển khai thật:

- `retrieval.py`: dense Qdrant Day 6, BM25, hybrid RRF, MMR, cross-encoder rerank, checksum embedding.
- `agent.py`: Ollama client và controller v1 để giữ khả năng đối chiếu.
- `agent_v2.py`: native search với bounded repair, query đầu gốc, citation alias ánh xạ ID Day06.
- `evaluation.py`: retrieval/context metrics sau generation, không đưa gold vào agent.
- `run.py`: benchmark dev/test, resume theo hash và kiểm tra freeze.
- `common.py`: đọc/ghi JSON UTF-8 và checksum.

Chạy từ root bằng `.venv/bin/python -m src.run --split dev` trong bản sao chưa
freeze, hoặc `scripts/ask.py` để hỏi một câu. Xem [cách chạy](../docs/RUNNING.md).
