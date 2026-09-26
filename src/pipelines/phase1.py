from __future__ import annotations

import logging

import pandas as pd

from core.config import load_settings
from core.utils import now_utc, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Xay dung baseline pipeline end-to-end cho Pha 1."""
    logger.info("=== BẮT ĐẦU PHA 1: BASELINE PIPELINE ===")
    settings = load_settings()
    run_date = now_utc()

    # 1. Ingestion
    logger.info("1/7. Ingestion: Lay metadata bai bao tu Crossref...")
    records = fetch_source_records(settings)
    logger.info(f"   -> Thu thap thanh cong {len(records)} raw records.")

    # 2. Cleaning & Modeling
    logger.info("2/7. Cleaning: Tien xu ly, khu trung lap va sinh text_for_embedding...")
    df = build_clean_dataframe(records, run_date)
    write_csv(df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, df.to_dict(orient="records"))
    logger.info(f"   -> Cleaned dataframe: {len(df)} dong hop le.")

    # 3. Observability Quality Gate & Freshness
    logger.info("3/7. Data Observability: Kiem dinh Great Expectations 1.x & Freshness...")
    quality = run_data_quality_checks(df, settings, "baseline")
    freshness = build_freshness_report(df, settings, settings.paths.freshness_report)
    logger.info(f"   -> Quality Gate Status: {quality['success']} (GX: {quality['gx_success']})")
    logger.info(f"   -> Freshness SLA Status: {freshness['is_fresh']} (Stale rows: {freshness['stale_rows']}/{freshness['total_rows']})")

    # 4. Build Vector Store Index (ChromaDB)
    logger.info("4/7. Vector Store: Indexing 24 documents vao Chroma collection 'papers-baseline'...")
    index = LocalEmbeddingIndex.build(df, settings, settings.paths.embeddings_json)
    logger.info("   -> Indexing hoan tat.")

    # 5. Build/Load Test Set
    logger.info("5/7. Test Set: Khoi tao bo 10 cau hoi benchmark...")
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        test_set = build_test_set(df, settings.paths.eval_testset)
        logger.info(f"   -> Sinh moi {len(test_set)} cau hoi.")
    else:
        logger.info(f"   -> Su dung test set co san tai {settings.paths.eval_testset}.")

    # 6. Evaluation
    logger.info("6/7. Evaluation: Danh gia Baseline RAG Retrieval va QA...")
    bundle = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )
    logger.info(f"   -> Baseline Retrieval Hit Rate: {bundle.summary['retrieval_hit_rate']:.2%}")
    logger.info(f"   -> Baseline Mean Token F1: {bundle.summary['mean_token_f1']:.4f}")
    logger.info(f"   -> Baseline Judge Accuracy: {bundle.summary['judge_accuracy']:.2%}")

    # 7. Generate Phase 1 Report
    logger.info("7/7. Reporting: Sinh bao cao Phase 1 Markdown...")
    source_summary = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "total_records": len(records),
        "clean_rows": len(df),
    }
    generate_phase1_report(settings.paths.baseline_report, source_summary, bundle.summary, quality, freshness)
    logger.info(f"   -> Bao cao da duoc luu tai {settings.paths.baseline_report}")
    logger.info("=== HOÀN TẤT PHA 1: BASELINE PIPELINE THÀNH CÔNG ===")


if __name__ == "__main__":
    main()
