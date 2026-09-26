# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| :--- | :--- |
| **Khóa/Lớp** | K4 - Lớp 3B |
| **Tên nhóm** | NGUYENKHANHDUY2403 |
| **Repository** | https://github.com/cvduynk-beep/K4-L3B-Day10-NGUYENKHANHDUY2403-Data-Pipeline-Data-Observability |
| **Ngày hoàn thành** | 2026-09-26 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Nguyễn Khánh Duy | 2403 | Full-pipeline Owner & Integrator | `crossref.py`, `cleaning.py`, `quality.py`, `testset.py`, `corruption.py`, `reporting.py`, `phase1.py`, `corruption_flow.py` |

---

## 2. Tóm tắt kết quả

Nhóm đã hoàn thành toàn diện chu trình Data Pipeline và Data Observability cho hệ thống RAG Agent phục vụ truy vấn metadata bài báo khoa học từ Crossref API. Trong pha Baseline, pipeline đã thu thập 24 bản ghi, làm sạch, tính toán `age_days`, tạo chuỗi `text_for_embedding` 5 phần, vượt qua 6 Expectations của Great Expectations 1.x (Status: PASS, Freshness SLA: Đạt) và đạt Retrieval Hit Rate 100.00%, Token F1 1.0000. 

Trong pha Corruption, khi tiêm 6 kịch bản lỗi (Drop latest records, Blank summary, Noise injection, Title truncation, Stale dates, Duplicate rows), Quality Gate đã phát hiện chính xác vi phạm (Status: FAIL, Freshness SLA: FAIL). Hiện tượng Silent Failure được chứng minh rõ nét khi Retrieval Hit Rate sụt giảm còn 60.00% và Token F1 tụt xuống 0.5741. Cơ chế Idempotent Repair sau đó tự động tái lập dữ liệu từ raw snapshot, đưa 100% các chỉ số kiểm định và chất lượng câu trả lời trở lại mức Baseline hoàn hảo. Toàn bộ quy trình được kiểm chứng tự động qua 2 entrypoints với exit code 0.

---

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API (hoặc local fallback snapshot)
    -> raw response & raw records (data/raw/)
    -> cleaning và data modeling (age_days, text_for_embedding 5 phần)
    -> embedding (all-MiniLM-L6-v2) + ChromaDB index (papers-baseline)
    -> evaluation baseline (test_set.json, 10 câu hỏi qua 4 categories)
    -> quality và freshness reports (GX 1.x ephemeral context)
    -> 6 kịch bản synthetic corruption
    -> re-index (papers-corrupted) và re-evaluate (corrupted metrics)
    -> idempotent repair từ raw records gốc
    -> re-index (papers-repaired) và re-evaluate (repaired metrics)
    -> comparison report (Baseline vs Corrupted vs Repaired)
```

---

## 4. Cách tái hiện kết quả

### Cấu hình môi trường

| Biến/cấu hình | Giá trị sử dụng |
| :--- | :--- |
| `LLM_PROVIDER` | `mock` (hoặc `gemini`) |
| `LLM_MODEL` | `gemini-2.5-flash` |
| Embedding model | `sentence-transformers/all-MiniLM-L6-v2` |
| Số lượng Crossref records | `24` |
| Retrieval `top_k` | `4` |
| Freshness threshold | `180` ngày |

### Lệnh chạy

1. Cài đặt môi trường:
   ```bash
   uv sync
   ```
2. Chạy Baseline Pipeline (Pha 1):
   ```bash
   python script/run_phase1.py
   ```
3. Chạy Corruption, Repair & So sánh (Pha 2):
   ```bash
   python script/run_corruption_flow.py
   ```

---

## 5. Bảng Đối Chiếu 3 Trạng Thái (Thực tế)

| Tiêu chí / Chỉ số đo lường | Baseline (Chuẩn) | Corrupted (Dữ liệu bẩn) | Repaired (Phục hồi) | Đánh giá & Xu hướng |
| :--- | :---: | :---: | :---: | :--- |
| **Số lượng bản ghi (Row Count)** | `24` | `22` | `24` | Khôi phục đầy đủ 24 bản ghi sạch |
| **Quality Gate (GX 1.x)** | **PASS (True)** | **FAIL (False)** | **PASS (True)** | Chốt chặn bắt trọn 6 lỗi vi phạm |
| **Freshness SLA (`is_fresh`)** | **PASS (True)** | **FAIL (False)** | **PASS (True)** | Bắt được tỷ lệ stale > 25% |
| **Retrieval Hit Rate** | **100.00%** | **60.00%** | **100.00%** | Sụt giảm mạnh (Silent Failure) và phục hồi |
| **Mean Token F1** | **1.0000** | **0.5741** | **1.0000** | Chất lượng câu trả lời phục hồi hoàn toàn |
| **Judge Accuracy** | **100.00%** | **60.00%** | **100.00%** | Tỷ lệ trả lời đúng lấy lại phong độ |
| **Mean Judge Score (1-5)** | **5.00** | **3.20** | **5.00** | Điểm số chất lượng khôi phục tuyệt đối |
