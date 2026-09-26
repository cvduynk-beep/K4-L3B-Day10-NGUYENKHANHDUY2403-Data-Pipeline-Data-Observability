# Báo Cáo Đối Chiếu 3 Trạng Thái: Baseline vs Corrupted vs Repaired

> **Mục đích:** Chứng minh năng lực phát hiện sự cố dữ liệu của Quality Gate (GX 1.x), đo lường mức độ suy giảm hiệu năng (Silent Failure) khi dữ liệu bị lỗi và kiểm chứng năng lực tự phục hồi (Idempotent Repair).

## 1. Bảng Tổng Hợp Đối Chiếu 3 Trạng Thái

| Tiêu chí / Chỉ số đo lường | Baseline (Chuẩn) | Corrupted (Dữ liệu bẩn) | Repaired (Phục hồi) | Đánh giá & Xu hướng |
| :--- | :---: | :---: | :---: | :--- |
| **Số lượng bản ghi (Row Count)** | `24` | `22` | `24` | Dữ liệu bị drop/duplicate được khôi phục chuẩn xác |
| **Quality Gate (GX 1.x)** | **PASS (True)** | **FAIL (False)** | **PASS (True)** | Quality Gate phát hiện trọn vẹn sự cố dữ liệu |
| **Freshness SLA (`is_fresh`)** | **True** | **FAIL (False)** | **True (True)** | Cảnh báo dữ liệu bị stale và trở lại bình thường |
| **Retrieval Hit Rate** | **100.00%** | **60.00%** | **100.00%** | Hiệu năng truy xuất phục hồi về mức đỉnh ban đầu |
| **Mean Token F1** | **1.0000** | **0.5741** | **1.0000** | Chất lượng câu trả lời phục hồi hoàn toàn |
| **Judge Accuracy** | **100.00%** | **60.00%** | **100.00%** | Tỷ lệ trả lời đúng lấy lại phong độ |
| **Mean Judge Score (1-5)** | **5.00** | **3.20** | **5.00** | Điểm số chất lượng khôi phục hoàn hảo |

## 2. Phân Tích Hiện Tượng Silent Failure Trên Corrupted Data
Khi tiêm 6 kịch bản lỗi vào dữ liệu sạch:
1. **Drop latest records (mất 20% bản ghi mới):** Làm cho RAG không thể tìm thấy context cho các câu hỏi liên quan đến tài liệu mới, khiến Retrieval Hit Rate sụt giảm nghiêm trọng.
2. **Blank summary:** Xóa rỗng context dẫn đến LLM không có thông tin để trả lời, kéo tụt điểm Token F1 xuống gần 0.
3. **Inject noise:** Ký tự rác làm nhiễu vector embeddings trong không gian cosine, khiến top-k trả về sai lệch hoặc câu trả lời bị nhiễm từ rác.
4. **Truncate title:** Làm hỏng cơ chế exact match và semantic match qua tiêu đề, khiến lookup thất bại.
5. **Stale date:** Đẩy lùi thời gian bài báo khiến tỷ lệ bài quá hạn > 25%, kích hoạt cảnh báo vi phạm Freshness SLA.
6. **Duplicate rows:** Phá vỡ tính toàn vẹn của primary key `paper_id`, vi phạm Expectation `ExpectColumnValuesToBeUnique`.

## 3. Cơ Chế Idempotent Repair & Tự Phục Hồi
- **Bảo toàn nguồn gốc (Data Lineage):** Nhờ lưu trữ bản snapshot thô gốc tại `data/raw/crossref_records.json`, hệ thống có thể tái lập pipeline làm sạch tại bất kỳ thời điểm nào.
- **Tính Idempotent:** Quy trình repair thực thi lại module cleaning chuẩn hóa, loại bỏ hoàn toàn các bản ghi trùng lặp và rác, nạp lại vector database trên Chroma collection riêng `papers-repaired`.
- **Kết luận:** Sau khi Repair, toàn bộ các chỉ số kiểm định chất lượng (GX 1.x) và hiệu năng truy vấn của Agent được phục hồi 100% về mức Baseline ban đầu.

---
*Báo cáo đối chiếu 3 trạng thái được sinh tự động bởi `script/run_corruption_flow.py`.*
