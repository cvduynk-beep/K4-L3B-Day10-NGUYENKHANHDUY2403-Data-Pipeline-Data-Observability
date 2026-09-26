from __future__ import annotations

from pathlib import Path
import time
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: Path) -> dict[str, Any]:
    """Tong hop freshness report."""
    total_rows = len(df)
    if total_rows == 0:
        report = {
            "latest_published": "N/A",
            "oldest_published": "N/A",
            "stale_rows": 0,
            "total_rows": 0,
            "stale_ratio": 0.0,
            "is_fresh": False,
            "freshness_threshold_days": settings.freshness_threshold_days,
        }
        write_json(report_path, report)
        return report

    latest_published = str(df["published"].max())
    oldest_published = str(df["published"].min())
    threshold = settings.freshness_threshold_days
    stale_rows = int((df["age_days"] > threshold).sum())
    stale_ratio = float(stale_rows / total_rows)
    # SLA Freshness: canh bao is_fresh = False neu ty le stale > 25%
    is_fresh = bool(stale_ratio <= 0.25)

    report = {
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "stale_ratio": round(stale_ratio, 4),
        "is_fresh": is_fresh,
        "freshness_threshold_days": threshold,
    }
    write_json(report_path, report)
    return report


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Tao bo data quality checks su dung Great Expectations 1.x ephemeral mode."""
    import great_expectations as gx
    import great_expectations.expectations as gxe

    context = gx.get_context(mode="ephemeral")
    source_name = f"papers_source_{report_name}_{int(time.time() * 1000)}"
    data_source = context.data_sources.add_pandas(name=source_name)
    data_asset = data_source.add_dataframe_asset(name="papers_asset")
    batch_def = data_asset.add_batch_definition_whole_dataframe("papers_batch")
    batch = batch_def.get_batch(batch_parameters={"dataframe": df})

    expectations = [
        gxe.ExpectTableRowCountToBeBetween(min_value=20, max_value=30),
        gxe.ExpectColumnValuesToNotBeNull(column="paper_id"),
        gxe.ExpectColumnValuesToNotBeNull(column="title"),
        gxe.ExpectColumnValuesToBeUnique(column="paper_id"),
        gxe.ExpectColumnValueLengthsToBeBetween(column="summary", min_value=50, max_value=5000),
        gxe.ExpectColumnValuesToNotBeNull(column="text_for_embedding"),
    ]

    suite = gx.ExpectationSuite(name=f"papers_suite_{report_name}_{int(time.time() * 1000)}")
    for exp in expectations:
        suite.add_expectation(exp)

    validation_result = batch.validate(suite)

    # Freshness check
    freshness_path = settings.paths.quality_dir / f"{report_name}_freshness.json" if report_name not in {"baseline", "test"} else settings.paths.freshness_report
    freshness = build_freshness_report(df, settings, freshness_path)

    check_details = []
    for res in validation_result.results:
        exp_type = getattr(res.expectation_config, "type", str(type(res.expectation_config)))
        kwargs = getattr(res.expectation_config, "kwargs", {})
        check_details.append(
            {
                "expectation_type": exp_type,
                "kwargs": {k: str(v) for k, v in kwargs.items()} if isinstance(kwargs, dict) else {},
                "success": bool(res.success),
                "result": {
                    "observed_value": res.result.get("observed_value") if isinstance(res.result, dict) else None,
                    "unexpected_count": res.result.get("unexpected_count", 0) if isinstance(res.result, dict) else 0,
                },
            }
        )

    overall_success = bool(validation_result.success and freshness["is_fresh"])

    quality_report = {
        "report_name": report_name,
        "success": overall_success,
        "gx_success": bool(validation_result.success),
        "total_checks": len(check_details),
        "passed_checks": sum(1 for c in check_details if c["success"]),
        "failed_checks": sum(1 for c in check_details if not c["success"]),
        "checks": check_details,
        "freshness": freshness,
    }

    if report_name == "baseline":
        out_path = settings.paths.baseline_quality_report
    elif report_name == "corrupted":
        out_path = settings.paths.corrupted_quality_report
    else:
        out_path = settings.paths.quality_dir / f"{report_name}_quality_report.json"

    write_json(out_path, quality_report)
    return quality_report
