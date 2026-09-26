# Báo Cáo Cá Nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| :--- | :--- |
| **Họ và tên** | Nguyễn Khánh Duy |
| **MSSV** | 2403 |
| **Khóa/Lớp** | K4 - Lớp 3B |
| **Tên nhóm** | NGUYENKHANHDUY2403 |
| **Vai trò chính** | Full-pipeline Owner & Lead Integrator |
| **Repository** | https://github.com/cvduynk-beep/K4-L3B-Day10-NGUYENKHANHDUY2403-Data-Pipeline-Data-Observability |
| **Ngày hoàn thành** | 2026-09-26 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **Raw Ingestion** | `src/ingestion/crossref.py` | Crossref API / local snapshot | `data/raw/crossref_records.json` | Hoàn thành |
| **Cleaning & Modeling** | `src/ingestion/cleaning.py` | Raw records | `data/clean/papers_clean.json`, `papers_clean.csv` | Hoàn thành |
| **Data Observability** | `src/observability/quality.py` | Cleaned/Corrupted DataFrame | `data/quality/*_quality_report.json`, `freshness_report.json` | Hoàn thành |
| **Evaluation Test Set** | `src/evaluation/testset.py` | Cleaned DataFrame | `data/eval/test_set.json` (10 câu hỏi) | Hoàn thành |
| **ChromaDB Vector Store** | `src/retrieval/index.py` | DataFrame, all-MiniLM-L6-v2 | 3 collections ChromaDB | Hoàn thành |
| **Corruption Suite** | `src/ingestion/corruption.py` | Cleaned DataFrame | `data/results/corruption_log.json` | Hoàn thành |
| **Orchestration & Reporting** | `src/pipelines/phase1.py`, `corruption_flow.py` | Toàn bộ các module | `baseline/corrupted/repaired_metrics.json`, `reports/*.md` | Hoàn thành |

---

## 3. Kết quả theo vai trò

- **Baseline Pipeline:** Đạt **100.00% Retrieval Hit Rate**, **1.0000 Mean Token F1**, Quality Gate trạng thái **PASS (True)** với 6 Expectations của Great Expectations 1.x.
- **Data Corruption:** Tiêm thành công 6 dạng lỗi (Drop 20% records, Blank summary, Noise injection, Title truncation, Stale date 500 days, Duplicate rows). Quality Gate chuyển trạng thái **FAIL (False)** và Freshness SLA báo **FAIL (False)**. Retrieval Hit Rate sụt giảm còn **60.00%**, Mean Token F1 sụt giảm còn **0.5741**.
- **Idempotent Repair:** Phục hồi toàn vẹn 24 bản ghi từ raw snapshot gốc, đưa Quality Gate trở lại **PASS (True)**, Retrieval Hit Rate trở lại **100.00%**, Mean Token F1 trở lại **1.0000**.
- **Báo cáo đối chiếu 3 trạng thái:** Tự động sinh báo cáo tại `data/reports/corruption_report.md` và `data/reports/phase1_report.md`.
