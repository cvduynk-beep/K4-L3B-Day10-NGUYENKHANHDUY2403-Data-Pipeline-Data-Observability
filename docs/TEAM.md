# Danh Sách Thành Viên & Báo Cáo Phân Công Nhóm

- **Tên Nhóm:** `NGUYENKHANHDUY2403`
- **Mã Nhóm / Lớp:** `K4-L3B-DAY10`
- **Tên Repository Nộp Bài:** `K4-L3B-Day10-NGUYENKHANHDUY2403-Data-Pipeline-Data-Observability`

---

## 1. Thành viên

| STT | Họ và tên | MSSV | Email | Vai trò & Phân công công việc | Báo cáo cá nhân |
|---:|---|---|---|---|---|
| 1 | Nguyễn Khánh Duy | 2403 | duynk@vinuni.edu.vn | Full-pipeline Owner & Integrator (`crossref.py`, `cleaning.py`, `quality.py`, `testset.py`, `corruption.py`, `reporting.py`, `phase1.py`, `corruption_flow.py`) | `report/2403_NguyenKhanhDuy.md` |

---

## 2. Báo cáo cá nhân

### Nguyễn Khánh Duy - MSSV: 2403
- **Vai trò:** Full-pipeline Owner & Lead Integrator.
- **Công việc chi tiết đã hoàn thành:**
  - Xây dựng module thu thập Crossref API với cơ chế fallback offline đọc từ local snapshot `data/raw/crossref_response.json` trong `src/ingestion/crossref.py`.
  - Khử trùng lặp theo `paper_id`, làm sạch thẻ JATS XML, chuẩn hóa whitespace, tính toán trường `age_days` và sinh chuỗi `text_for_embedding` 5 phần chuẩn hóa trong `src/ingestion/cleaning.py`.
  - Cấu hình chốt kiểm dịch chất lượng dữ liệu theo chuẩn mới **Great Expectations 1.x Ephemeral Context** và giám sát Freshness SLA (ngưỡng 180 ngày) trong `src/observability/quality.py`.
  - Thiết lập bộ câu hỏi đánh giá chuẩn 10 câu qua 4 nhóm nghiệp vụ (`summary`, `authors`, `date`, `categories`) trong `src/evaluation/testset.py`.
  - Quản lý mô hình embedding `sentence-transformers/all-MiniLM-L6-v2` và nạp 3 collection riêng biệt trong ChromaDB (`papers-baseline`, `papers-corrupted`, `papers-repaired`).
  - Triển khai đầy đủ 6 kịch bản làm bẩn dữ liệu trong `src/ingestion/corruption.py`, đo lường sự sụt giảm hiệu năng (Silent Failure) và thiết kế cơ chế tự phục hồi (Idempotent Repair) từ raw snapshot gốc.
  - Kết nối toàn bộ luồng thực thi trong `src/pipelines/phase1.py` và `src/pipelines/corruption_flow.py`, xuất bảng đối chiếu 3 trạng thái vào `data/reports/corruption_report.md`.
- **Điều học được / Đóng góp chính:**
  - Nắm vững kiến trúc Data Observability cho hệ thống RAG trong sản xuất, hiểu cách ngăn chặn hiện tượng Silent Failure trước khi dữ liệu đi vào serving layer và kỹ thuật thiết kế Idempotent Pipeline đảm bảo tính toàn vẹn dữ liệu.
