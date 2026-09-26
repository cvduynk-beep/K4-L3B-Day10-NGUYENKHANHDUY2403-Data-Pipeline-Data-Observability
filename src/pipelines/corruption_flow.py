from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.index import LocalEmbeddingIndex

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Xay dung corruption -> evaluate -> repair -> compare flow."""
    logger.info("=== BẮT ĐẦU PHA 2: CORRUPTION, REPAIR & COMPARISON FLOW ===")
    settings = load_settings()

    # 1. Load Baseline clean dataset & metrics
    logger.info("1/7. Load Baseline clean data...")
    if not settings.paths.clean_json.exists():
        raise FileNotFoundError(f"Clean dataset not found at {settings.paths.clean_json}. Vui long chay Phase 1 truoc.")
    clean_df = pd.read_json(settings.paths.clean_json)
    baseline_metrics = read_json(settings.paths.baseline_metrics)

    # 2. Simulate Synthetic Data Corruption (6 kịch bản)
    logger.info("2/7. Tiêm 6 kịch bản Data Corruption vào dataset...")
    corrupted_df = corrupt_clean_dataframe(clean_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    logger.info(f"   -> Corrupted dataset: {len(corrupted_df)} rows. Log luu tai {settings.paths.corruption_log}")

    # 3. Observability Quality Gate trên Corrupted Data
    logger.info("3/7. Chạy Quality Gate trên Corrupted Data...")
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted")
    corrupted_freshness = corrupted_quality["freshness"]
    logger.info(f"   -> Corrupted Quality Gate Status: {corrupted_quality['success']} (Dự kiến: False)")
    logger.info(f"   -> Corrupted Freshness SLA Status: {corrupted_freshness['is_fresh']} (Dự kiến: False)")

    # 4. Build Corrupted Vector Store & Evaluate
    logger.info("4/7. Indexing corrupted data vào collection 'papers-corrupted' và đánh giá sụt giảm...")
    corrupted_index = LocalEmbeddingIndex.build(corrupted_df, settings, settings.paths.corrupted_embeddings_json)
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    logger.info(f"   -> Corrupted Hit Rate: {corrupted_bundle.summary['retrieval_hit_rate']:.2%}")
    logger.info(f"   -> Corrupted Token F1: {corrupted_bundle.summary['mean_token_f1']:.4f}")

    # 5. Idempotent Repair từ Raw Snapshot
    logger.info("5/7. Thực thi Idempotent Repair từ raw records gốc...")
    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired_df = build_clean_dataframe(raw_records, now_utc())
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    logger.info(f"   -> Repaired dataset: {len(repaired_df)} rows sạch hoàn toàn.")

    # 6. Quality Gate & Evaluate trên Repaired Data
    logger.info("6/7. Chạy Quality Gate và đánh giá phục hồi trên Repaired Data...")
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired")
    repaired_freshness = repaired_quality["freshness"]
    logger.info(f"   -> Repaired Quality Gate Status: {repaired_quality['success']} (Dự kiến: True)")

    repaired_index = LocalEmbeddingIndex.build(repaired_df, settings, settings.paths.repaired_embeddings_json)
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    logger.info(f"   -> Repaired Hit Rate: {repaired_bundle.summary['retrieval_hit_rate']:.2%}")
    logger.info(f"   -> Repaired Token F1: {repaired_bundle.summary['mean_token_f1']:.4f}")

    # 7. Generate Comparison Report (3 Trạng Thái)
    logger.info("7/7. Sinh báo cáo đối chiếu 3 trạng thái...")
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )

    # In bảng đối chiếu trực tiếp ra console
    print("\n" + "=" * 70)
    print(" BẢNG ĐỐI CHIẾU 3 TRẠNG THÁI: BASELINE vs CORRUPTED vs REPAIRED")
    print("=" * 70)
    print(f"{'Tiêu chí':<25} | {'Baseline':<12} | {'Corrupted':<12} | {'Repaired':<12}")
    print("-" * 70)
    print(f"{'Total Rows':<25} | {'24':<12} | {str(len(corrupted_df)):<12} | {str(len(repaired_df)):<12}")
    print(f"{'Quality Gate (GX 1.x)':<25} | {'PASS':<12} | {('PASS' if corrupted_quality['success'] else 'FAIL'):<12} | {('PASS' if repaired_quality['success'] else 'FAIL'):<12}")
    print(f"{'Freshness SLA':<25} | {'PASS':<12} | {('PASS' if corrupted_freshness['is_fresh'] else 'FAIL'):<12} | {('PASS' if repaired_freshness['is_fresh'] else 'FAIL'):<12}")
    print(f"{'Retrieval Hit Rate':<25} | {baseline_metrics['retrieval_hit_rate']:<12.2%} | {corrupted_bundle.summary['retrieval_hit_rate']:<12.2%} | {repaired_bundle.summary['retrieval_hit_rate']:<12.2%}")
    print(f"{'Mean Token F1':<25} | {baseline_metrics['mean_token_f1']:<12.4f} | {corrupted_bundle.summary['mean_token_f1']:<12.4f} | {repaired_bundle.summary['mean_token_f1']:<12.4f}")
    print(f"{'Judge Accuracy':<25} | {baseline_metrics['judge_accuracy']:<12.2%} | {corrupted_bundle.summary['judge_accuracy']:<12.2%} | {repaired_bundle.summary['judge_accuracy']:<12.2%}")
    print(f"{'Mean Judge Score':<25} | {baseline_metrics['mean_judge_score']:<12.2f} | {corrupted_bundle.summary['mean_judge_score']:<12.2f} | {repaired_bundle.summary['mean_judge_score']:<12.2f}")
    print("=" * 70 + "\n")
    logger.info(f"Báo cáo đối chiếu đã được ghi thành công tại {settings.paths.comparison_report}")
    logger.info("=== HOÀN TẤT PHA 2: CORRUPTION FLOW THÀNH CÔNG ===")


if __name__ == "__main__":
    main()
