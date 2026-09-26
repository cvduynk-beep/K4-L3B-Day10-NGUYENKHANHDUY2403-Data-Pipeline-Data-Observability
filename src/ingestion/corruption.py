from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import write_json


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: Path | str) -> pd.DataFrame:
    """Simulate 6 dang data corruption theo yeu cau de bai:

    1. Drop latest records (mat 20% ban ghi moi).
    2. Blank summary o mot so dong.
    3. Inject noise vao summary.
    4. Lam title bi truncate (< 8 ky tu).
    5. Lam published date cu di (lui 500 ngay de vi pham Freshness SLA).
    6. Add duplicate rows (vi pham unique paper_id).
    7. Rebuild `text_for_embedding`.
    8. Ghi corruption log vao output_log_path.
    """
    corrupted_df = df.copy()
    logs: list[dict[str, Any]] = []

    # 1. Drop latest 20% records (khoang 5 records neu tong 24)
    drop_count = max(1, int(len(corrupted_df) * 0.20))
    dropped_rows = corrupted_df.iloc[:drop_count]
    dropped_ids = dropped_rows["paper_id"].tolist()
    corrupted_df = corrupted_df.iloc[drop_count:].copy().reset_index(drop=True)
    logs.append(
        {
            "scenario": "drop_latest_records",
            "description": f"Dropped {drop_count} latest records ({drop_count / len(df):.0%})",
            "affected_ids": dropped_ids,
        }
    )

    # 2. Blank summary o 2 dong
    blank_indices = [0, 1] if len(corrupted_df) >= 2 else [0]
    blank_ids = []
    for idx in blank_indices:
        corrupted_df.loc[idx, "summary"] = ""
        corrupted_df.loc[idx, "summary_chars"] = 0
        blank_ids.append(str(corrupted_df.loc[idx, "paper_id"]))
    logs.append(
        {
            "scenario": "blank_summary",
            "description": f"Blanked summary for {len(blank_ids)} records",
            "affected_ids": blank_ids,
        }
    )

    # 3. Inject noise vao summary o 2 dong
    noise_indices = [2, 3] if len(corrupted_df) >= 4 else []
    noise_ids = []
    noise_payload = " [CORRUPTED_NOISE_$%#@! INVALID_VECTOR_EMBEDDING] "
    for idx in noise_indices:
        orig = str(corrupted_df.loc[idx, "summary"])
        corrupted_df.loc[idx, "summary"] = f"{noise_payload} {orig} {noise_payload}"
        corrupted_df.loc[idx, "summary_chars"] = len(corrupted_df.loc[idx, "summary"])
        noise_ids.append(str(corrupted_df.loc[idx, "paper_id"]))
    logs.append(
        {
            "scenario": "inject_noise",
            "description": f"Injected noise tokens into summary for {len(noise_ids)} records",
            "affected_ids": noise_ids,
        }
    )

    # 4. Truncate title < 8 ky tu o 2 dong
    trunc_indices = [4, 5] if len(corrupted_df) >= 6 else []
    trunc_ids = []
    for idx in trunc_indices:
        corrupted_df.loc[idx, "title"] = "Bad"
        trunc_ids.append(str(corrupted_df.loc[idx, "paper_id"]))
    logs.append(
        {
            "scenario": "truncate_title",
            "description": f"Truncated title to '< 8 chars' for {len(trunc_ids)} records",
            "affected_ids": trunc_ids,
        }
    )

    # 5. Stale date (lui 500 ngay o 8 dong de > 25% tong so bai bi stale)
    stale_count = min(8, len(corrupted_df))
    stale_ids = []
    for idx in range(stale_count):
        try:
            pub_date = datetime.strptime(str(corrupted_df.loc[idx, "published"])[:10], "%Y-%m-%d").date()
            new_date = pub_date - timedelta(days=500)
            corrupted_df.loc[idx, "published"] = new_date.isoformat()
            corrupted_df.loc[idx, "age_days"] = int(corrupted_df.loc[idx, "age_days"]) + 500
            stale_ids.append(str(corrupted_df.loc[idx, "paper_id"]))
        except Exception:
            pass
    logs.append(
        {
            "scenario": "stale_date",
            "description": f"Shifted publication date back by 500 days for {len(stale_ids)} records (violating Freshness SLA)",
            "affected_ids": stale_ids,
        }
    )

    # 6. Add duplicate rows (nhan doi 2 dong)
    dup_rows = corrupted_df.iloc[:2].copy()
    dup_ids = dup_rows["paper_id"].tolist()
    corrupted_df = pd.concat([corrupted_df, dup_rows], ignore_index=True)
    logs.append(
        {
            "scenario": "duplicate_rows",
            "description": f"Duplicated {len(dup_ids)} rows, creating duplicate paper_id",
            "affected_ids": dup_ids,
        }
    )

    # 7. Rebuild text_for_embedding cho toan bo cac dong
    text_embeddings = []
    for _, row in corrupted_df.iterrows():
        t = (
            f"Title: {row['title']}\n"
            f"Authors: {row['authors_joined']}\n"
            f"Categories: {row['categories_joined']}\n"
            f"Published Date: {row['published']}\n"
            f"Summary: {row['summary']}"
        )
        text_embeddings.append(t)
    corrupted_df["text_for_embedding"] = text_embeddings

    # 8. Ghi corruption log
    out_p = Path(output_log_path)
    write_json(
        out_p,
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "original_rows": len(df),
            "corrupted_rows": len(corrupted_df),
            "scenarios": logs,
        },
    )

    return corrupted_df
