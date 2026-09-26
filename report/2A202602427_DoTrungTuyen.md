# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Đỗ Trung Tuyến            |
| MSSV               | 2A202602427               |
| Khóa/Lớp         | K4 - Lớp B (Ca Sáng)      |
| Tên nhóm         | Team 03 - DataObservability |
| Vai trò chính    | RAG Agent & Vector Index Architecture |
| Repository         | K4-L3B-DAY10-Team03-DataPipelineDataObservability |
| Ngày hoàn thành | 2026-09-26               |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái |
| ------------------ | --------------------- | ---------------- | ----------------- | ---------- |
| Vector Index & ChromaDB Collections | `src/retrieval/index.py` (`LocalEmbeddingIndex.build`, `search`, `lookup`) | Cleaned/Corrupted/Repaired DataFrame | 3 collections độc lập trong ChromaDB (`papers-baseline`, `papers-corrupted`, `papers-repaired`) | Hoàn thành |
| Sentence Embeddings Normalization | `src/retrieval/embeddings.py` (`MiniLMEmbeddings`) | Danh sách văn bản 5 phần (`text_for_embedding`) | Vector nhúng 384 chiều chuẩn hóa L2, manifest JSON | Hoàn thành |
| Multi-Provider LLM Factory | `src/retrieval/llm.py` (`build_llm`) | Cấu hình `Settings`, `LLM_PROVIDER` | Instance ChatModel tương ứng (`gemini`, `openai`, `anthropic`, `mock`) | Hoàn thành |
| Question Answering & Context Extraction | `src/retrieval/qa.py` (`answer_question`, `_extract_answer`) | Câu hỏi, `LocalEmbeddingIndex` | Đối tượng `AnswerResult` với câu trả lời và doc_ids trích xuất | Hoàn thành |
| LangChain Retrieval Agent | `src/retrieval/agent.py` (`build_agent`, `run_agent_question`) | `LocalEmbeddingIndex`, LLM Model | Agent kết hợp 2 tools: `semantic_search_papers` và `lookup_paper` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --------- | ----------------------------- | ------- |
| Tối ưu cấu trúc `text_for_embedding` | Đặng Thái Anh (`cleaning.py`) | Đưa 5 trường cốt lõi (Title, Authors, Categories, Published, Summary) vào chuỗi nhúng giúp vector phân tách rõ rệt |
| Đo lường ảnh hưởng của lỗi dữ liệu lên Vector Search | Nguyễn Khánh Duy (`metrics.py`) | Phân tích cơ chế khiến Hit Rate tụt từ 100% xuống 60% khi tóm tắt bị rỗng hoặc nhiễu |
| Kiểm thử cô lập Vector Index trong Pytest | Nguyễn Đức Anh (`tests/test_pipeline.py`) | Viết unit tests kiểm thử khởi tạo index, embedding, và similarity search |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --------------------- | --------------------------- | ---------------- | ------------- |
| Thiết lập ChromaDB Collections độc lập | `src/retrieval/index.py` | 3 collections riêng biệt trong thư mục `data/chroma/` | Gọi `PersistentClient.get_collection()` cho từng tên |
| Tích hợp mô hình `all-MiniLM-L6-v2` | `src/retrieval/embeddings.py` | Khởi tạo mô hình offline với bộ nhớ đệm `@lru_cache` | Vector embedding 384-d, `np.linalg.norm == 1.0` |
| Xây dựng Multi-Provider LLM Router | `src/retrieval/llm.py` | Chuyển đổi linh hoạt giữa Gemini, OpenAI, Anthropic, Mock | Chạy test suite với `LLM_PROVIDER=mock` không cần API Key |
| Trích xuất câu trả lời chuẩn xác ngữ cảnh | `src/retrieval/qa.py` | Exact title match kết hợp semantic search | Trả lời chính xác 10/10 câu hỏi test benchmark (Baseline) |

**Output cụ thể:**
Hệ thống vector index tại `data/chroma/` cùng các manifest tương ứng (`papers_embeddings.json`, `papers_embeddings_corrupted.json`, `papers_embeddings_repaired.json`) ghi nhận đầy đủ 24 documents với siêu dữ liệu phục vụ truy vấn.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
1. **Xung đột Vector Cache (Collection Collision):** Nếu dùng chung một ChromaDB collection cho cả 3 trạng thái (Baseline, Corrupted, Repaired), bộ đệm HNSW in-memory sẽ làm rò rỉ dữ liệu cũ sang dữ liệu mới, khiến việc đo lường suy thoái bị sai lệch.
2. **Cân bằng giữa Exact Lookup và Semantic Retrieval:** Các câu hỏi thực tế có thể tìm theo tên chính xác của bài báo hoặc tìm theo ý nghĩa nội dung. Cần kết hợp cả hai cơ chế để tối ưu hóa Retrieval Hit Rate.
3. **Môi trường CI không có API Key thương mại:** Cần một mock provider nhẹ nhàng để kiểm thử tự động mà không phụ thuộc vào kết nối Internet hay chi phí gọi API bên ngoài.

### Cách triển khai
1. **Cô lập Vector Index (Vector Space Isolation):**
   Trong `LocalEmbeddingIndex._derive_collection_name`, hệ thống ánh xạ đường dẫn lưu manifest với tên collection tương ứng:
   - `papers_embeddings.json` $\rightarrow$ `papers-baseline`
   - `papers_embeddings_corrupted.json` $\rightarrow$ `papers-corrupted`
   - `papers_embeddings_repaired.json` $\rightarrow$ `papers-repaired`
   Mỗi lần build lại collection, hàm `build()` thực hiện `client.delete_collection()` nếu đã tồn tại để đảm bảo tính Idempotent.
2. **Chuẩn hóa Cosine Space:**
   Khởi tạo collection với cấu hình:
   ```python
   collection = client.create_collection(
       name=collection_name,
       configuration={"hnsw": {"space": "cosine"}},
   )
   ```
   Kết hợp với `normalize_embeddings=True` trong `SentenceTransformer.encode()`, khoảng cách cosine phản ánh chính xác độ tương đồng ngữ nghĩa.
3. **Cơ chế Hybrid Lookup trong QA Agent:**
   Trong `answer_question()`, hệ thống trích xuất tên bài báo từ dấu nháy đơn (`'...'`) bằng Regex để tra cứu trực tiếp trong từ điển `documents_by_title`. Nếu tìm thấy, tài liệu này được ưu tiên đặt ở vị trí Top 1 với điểm số 1.0, sau đó bổ sung thêm các kết quả từ semantic search.

### Input, output và contract

| Thành phần | Mô tả |
| ---------- | ----- |
| Input | DataFrame cleaned/corrupted/repaired có cột `text_for_embedding`, `paper_id`, `title` |
| Output | `LocalEmbeddingIndex` instance, ChromaDB collection trên ổ đĩa, `SearchResult`, `AnswerResult` |
| Module phụ thuộc | `ingestion/cleaning.py` (cột `text_for_embedding`), `core/config.py` |
| Module sử dụng output | `evaluation/metrics.py`, `pipelines/phase1.py`, `pipelines/corruption_flow.py` |
| Điều kiện lỗi cần xử lý | Collection đã tồn tại khi build lại, ký tự đặc biệt trong query, API key thiếu khi chọn provider thương mại |

### Cách xác minh

```bash
python -c "from core.config import load_settings; from retrieval.index import LocalEmbeddingIndex; import pandas as pd; s=load_settings(); df=pd.read_json(s.paths.clean_json); idx=LocalEmbeddingIndex.build(df, s); res=idx.search('machine learning', top_k=2); print(f'Tín hiệu hoàn thành: Tim thay {len(res)} ket qua, top 1: {res[0].title}')"
```

- **Kết quả mong đợi:** Tìm thấy 2 kết quả và in ra tiêu đề bài báo phù hợp nhất.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn giữa việc xóa/ghi đè cùng 1 collection trong ChromaDB hay phân tách thành 3 collection độc lập cho 3 trạng thái (Baseline, Corrupted, Repaired).
- **Các phương án đã cân nhắc:**
  - *Phương án 1:* Dùng duy nhất một collection `papers-main`, mỗi pha xóa đi nạp lại dữ liệu tương ứng.
  - *Phương án 2:* Thiết lập 3 collection độc lập: `papers-baseline`, `papers-corrupted`, và `papers-repaired`.
- **Phương án đã chọn:** Phương án 2 (3 collection độc lập).
- **Lý do:** ChromaDB sử dụng cơ chế lưu chỉ mục HNSW trên ổ đĩa kèm bộ nhớ đệm in-process. Khi xóa và tạo lại cùng một tên collection liên tục trong cùng một tiến trình Python, ChromaDB đôi khi dính lỗi `Internal ChromaDB index cache state collision`, dẫn tới việc các vector cũ chưa được giải phóng hoàn toàn khỏi RAM. Việc phân tách 3 tên collection riêng biệt giúp cô lập hoàn toàn không gian vector, đảm bảo kết quả đánh giá giữa 3 pha là hoàn toàn độc lập và trung thực.
- **Bằng chứng quyết định phù hợp:** Toàn bộ pipeline `run_corruption_flow.py` chạy mượt mà, không gặp bất kỳ lỗi xung đột collection nào và chỉ số phản ánh đúng 100% bản chất suy thoái dữ liệu.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:**
  ```text
  chromadb.errors.UniqueConstraintError: Collection papers-baseline already exists
  ```
- **Lệnh tái hiện:** Chạy lại `python script/run_phase1.py` lần thứ 2 khi thư mục `data/chroma/` đã tồn tại từ lần chạy trước.
- **Nguyên nhân gốc:** Hàm `client.create_collection(name=collection_name)` mặc định ném ra `UniqueConstraintError` nếu collection có cùng tên đã tồn tại trong database SQLite của ChromaDB.
- **Cách xử lý:** 
  Trong hàm `LocalEmbeddingIndex.build()`, thực hiện xóa collection cũ trước khi tạo mới:
  ```python
  try:
      client.delete_collection(name=collection_name)
  except Exception:
      pass
  collection = client.create_collection(
      name=collection_name,
      configuration={"hnsw": {"space": "cosine"}},
  )
  ```
- **Cách xác minh sau khi sửa:** Chạy lặp lại `run_phase1.py` và `run_corruption_flow.py` nhiều lần liên tiếp, script luôn thực thi hoàn hảo với tính chất Idempotent (chạy bao nhiêu lần kết quả vẫn nhất quán).
- **Điều học được:** Khi xây dựng Data Pipeline cho Vector Database, luôn phải thiết kế theo nguyên tắc Idempotent: dọn dẹp trạng thái cũ trước khi nạp trạng thái mới để tránh xung đột dữ liệu.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Crossref REST API cung cấp metadata bài báo $\rightarrow$ raw snapshot lưu trữ để đảm bảo data lineage $\rightarrow$ module cleaning trích xuất và ghép thành chuỗi `text_for_embedding` gồm 5 phần chuẩn mực $\rightarrow$ `MiniLMEmbeddings` mã hóa thành vector 384 chiều $\rightarrow$ ChromaDB lưu vector kèm metadata (`paper_id`, `title`, `summary`, `authors`, `published`) theo cấu trúc chỉ mục HNSW.
2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   Mỗi câu hỏi trong test set gắn liền với `ground_truth_doc_ids` (bài báo chứa câu trả lời). Trong quá trình truy vấn, hệ thống lấy Top 4 tài liệu gần nhất từ ChromaDB. Nếu `ground_truth_doc_ids` nằm trong 4 tài liệu này, truy vấn được tính là Retrieval Hit. Độ tương đồng giữa câu trả lời sinh ra và `ground_truth` được đo bằng Token F1 và LLM Judge.
3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   Quality checks (Great Expectations 1.x) kiểm soát tính toàn vẹn của dữ liệu tại một thời điểm (schema, non-null, uniqueness, độ dài văn bản). Freshness monitoring kiểm soát sự suy giảm giá trị của dữ liệu theo thời gian (Data Drift / Stale Data), đảm bảo các bài báo trong hệ thống luôn đáp ứng SLA (tỷ lệ bài quá 180 ngày không vượt quá 25%).
4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Để duy trì biến kiểm soát (control variable) duy nhất là **chất lượng dữ liệu**. Nếu thay đổi câu hỏi, sự thay đổi điểm số có thể do độ khó của câu hỏi chứ không phản ánh được tác động của dữ liệu bẩn.
5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   - Về dữ liệu: `papers_clean_repaired.json` có đủ 24 bản ghi sạch, `repaired_quality_report.json` đạt `success=True`, `repaired_freshness_report.json` đạt `is_fresh=True`.
   - Về hiệu năng: `repaired_metrics.json` có `retrieval_hit_rate` phục hồi từ 60.0% lên 100.0% và `mean_token_f1` phục hồi từ 85.1% lên 100.0%.

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate`   |   100.0% |     60.0% |   100.0% | Sụt giảm 40% do 4 bài báo mới bị drop và tóm tắt bị hỏng |
| `mean_token_f1`        |   100.0% |     85.1% |   100.0% | Điểm F1 giảm mạnh ở các câu hỏi tóm tắt bị tiêm nhiễu |
| `judge_accuracy`       |   100.0% |     90.0% |   100.0% | 1 câu hỏi bị đánh giá sai do thông tin tóm tắt bị mất |
| `mean_judge_score`     |     5.00 |      4.20 |     5.00 | Giảm 0.80 điểm trên thang điểm 5 của LLM Judge |
| Quality checks         |   PASSED |    FAILED |   PASSED | Bị fail do duplicate ID và title quá ngắn (< 8 chars) |
| Freshness status       |  HEALTHY |  VIOLATED |  HEALTHY | Tỷ lệ stale 40.9% vi phạm nghiêm trọng ngưỡng 25% |

### Kết luận từ số liệu
- Kết quả thực nghiệm chứng minh rằng chất lượng của mô hình Vector Embedding và Agent RAG phụ thuộc trực tiếp vào độ sạch của dữ liệu đầu vào (Garbage In, Garbage Out).
- Khi dữ liệu bị tiêm lỗi, hiện tượng **Silent Failure** xảy ra: hệ thống vẫn hoạt động bình thường, không báo lỗi runtime, nhưng chất lượng tìm kiếm ngữ nghĩa bị tê liệt nghiêm trọng (Hit Rate giảm 40%).
- Cơ chế Idempotent Repair và tái tạo ChromaDB collection khôi phục hoàn hảo 100% độ chính xác của hệ thống RAG.

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1. **Kiến trúc Vector Database phân tầng:** Hiểu rõ cách ChromaDB tổ chức collection, embedding function và chỉ mục HNSW để tránh xung đột dữ liệu.
2. **Tác động của cấu trúc dữ liệu nhúng:** Việc thiết kế chuỗi văn bản nhúng có cấu trúc (Title, Authors, Categories, Published, Summary) mang lại độ phân tách ngữ nghĩa vượt trội so với việc nhúng văn bản thô.
3. **Tầm quan trọng của Silent Failure Detection:** Nhận thức rõ ràng rằng code chạy không lỗi không đồng nghĩa với việc AI hoạt động đúng. Data Observability là tấm khiên bắt buộc cho mọi hệ thống AI hiện đại.

### Nếu có thêm thời gian
Tôi sẽ tích hợp thêm cơ chế **Hybrid Search (Sparse + Dense)** kết hợp BM25 và MiniLM Embedding với thuật toán Reciprocal Rank Fusion (RRF) để tối ưu hơn nữa khả năng tìm kiếm đối với các từ khóa chuyên ngành hiếm gặp.

---

## 10. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đỗ Trung Tuyến  
**Ngày xác nhận:** 2026-09-26
