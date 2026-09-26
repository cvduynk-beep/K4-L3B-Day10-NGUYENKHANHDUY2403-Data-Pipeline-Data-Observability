# Báo Cáo Pha 1 — Baseline Data Pipeline & Observability

## 1. Nguồn Thu Thập Dữ Liệu (Crossref API Ingestion)
- **Nguồn dữ liệu:** Crossref REST API
- **Query truy vấn:** `agentic retrieval augmented generation large language model`
- **Bộ lọc thời gian:** `from-pub-date:2026-03-30,has-abstract:true`
- **Tổng số bài báo thu thập:** `24`
- **Trạng thái làm sạch (Clean rows):** `24` bản ghi
- **Cơ chế Fallback:** Đọc từ local snapshot `data/raw/crossref_response.json` khi có sự cố mạng hoặc 429.

## 2. Kết Quả Kiểm Định Chất Lượng Dữ Liệu (Great Expectations 1.x)
- **Trạng thái Quality Gate:** **PASS (True)**
- **Tổng số kiểm định (Expectations):** `6`
- **Số kiểm định đạt (Passed):** `6`
- **Số kiểm định trượt (Failed):** `0`

| STT | Expectation | Kết quả | Chi tiết |
| :---: | :--- | :---: | :--- |
| 1 | `expect_table_row_count_to_be_between` | **PASSED** | `{'batch_id': 'papers_source_baseline_1790393711769-papers_asset', 'min_value': '20', 'max_value': '30'}` |
| 2 | `expect_column_values_to_not_be_null` | **PASSED** | `{'batch_id': 'papers_source_baseline_1790393711769-papers_asset', 'column': 'paper_id'}` |
| 3 | `expect_column_values_to_be_unique` | **PASSED** | `{'batch_id': 'papers_source_baseline_1790393711769-papers_asset', 'column': 'paper_id'}` |
| 4 | `expect_column_values_to_not_be_null` | **PASSED** | `{'batch_id': 'papers_source_baseline_1790393711769-papers_asset', 'column': 'title'}` |
| 5 | `expect_column_value_lengths_to_be_between` | **PASSED** | `{'batch_id': 'papers_source_baseline_1790393711769-papers_asset', 'column': 'summary', 'min_value': '50', 'max_value': '5000'}` |
| 6 | `expect_column_values_to_not_be_null` | **PASSED** | `{'batch_id': 'papers_source_baseline_1790393711769-papers_asset', 'column': 'text_for_embedding'}` |

## 3. Giám Sát Freshness SLA
- **Ngưỡng quá hạn (SLA Threshold):** `180` ngày
- **Bài báo mới nhất:** `2026-07-22`
- **Bài báo cũ nhất:** `2026-03-28`
- **Số bài quá hạn (Stale rows):** `1 / 24`
- **Tỷ lệ quá hạn:** `4.17%`
- **Đạt chuẩn Freshness SLA:** **ĐẠT (True)**

## 4. Hiệu Năng RAG Retrieval & QA Baseline
| Chỉ số đánh giá | Giá trị Baseline | Diễn giải |
| :--- | :---: | :--- |
| **Retrieval Hit Rate** | **100.00%** | Tỷ lệ tìm đúng tài liệu chứa đáp án trong Top-K |
| **Mean Token F1** | **1.0000** | Độ trùng khớp từ ngữ giữa câu trả lời và Ground Truth |
| **Judge Accuracy** | **100.00%** | Tỷ lệ câu trả lời được giám khảo đánh giá chính xác |
| **Mean Judge Score (1-5)** | **5.00 / 5.0** | Điểm số đánh giá chất lượng câu trả lời |
| **Tổng số câu hỏi đánh giá** | `10` | Bộ test set chuẩn hóa phủ 4 nhóm nghiệp vụ |

---
*Báo cáo được tự động khởi tạo bởi pipeline Data Observability.*
