from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

import pandas as pd

from core.utils import compact_join, normalize_whitespace
from ingestion.crossref import PaperRecord


def _strip_xml_tags(text: str) -> str:
    cleaned = re.sub(r"<[^>]+>", "", text)
    return normalize_whitespace(cleaned)


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records thanh dataframe san sang de embed.

    1. Normalize title, summary, authors, categories.
    2. Parse published/updated date.
    3. Tinh age_days = (run_date - published).days.
    4. Tao cot helper:
       - authors_joined
       - categories_joined
       - summary_chars
       - text_for_embedding (cau truc 5 phan chuan)
    5. Drop duplicates theo paper_id va filter row xau.
    6. Sort dataframe va return.
    """
    seen_ids: set[str] = set()
    rows: list[dict[str, Any]] = []

    if run_date.tzinfo is None:
        target_date = run_date.date()
    else:
        target_date = run_date.astimezone(timezone.utc).date()

    for record in records:
        pid = record.paper_id.strip()
        if not pid or pid in seen_ids:
            continue

        title = _strip_xml_tags(record.title)
        summary = _strip_xml_tags(record.summary)

        if not title or not summary:
            continue

        seen_ids.add(pid)

        authors = [normalize_whitespace(a) for a in record.authors if normalize_whitespace(a)]
        categories = [normalize_whitespace(c) for c in record.categories if normalize_whitespace(c)]
        authors_joined = compact_join(authors, sep=", ")
        categories_joined = compact_join(categories, sep=", ")

        published_str = record.published.strip()[:10]
        try:
            pub_date = datetime.strptime(published_str, "%Y-%m-%d").date()
            age_days = max(0, (target_date - pub_date).days)
        except Exception:
            pub_date = target_date
            age_days = 0

        # Cấu trúc 5 phần chuẩn theo Rubric
        text_for_embedding = (
            f"Title: {title}\n"
            f"Authors: {authors_joined}\n"
            f"Categories: {categories_joined}\n"
            f"Published Date: {published_str}\n"
            f"Summary: {summary}"
        )

        rows.append(
            {
                "paper_id": pid,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": record.primary_category or (categories[0] if categories else "Unknown"),
                "published": published_str,
                "updated": record.updated.strip()[:10] if record.updated else published_str,
                "abs_url": record.abs_url,
                "pdf_url": record.pdf_url,
                "comment": record.comment,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": len(summary),
                "age_days": age_days,
                "text_for_embedding": text_for_embedding,
            }
        )

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(by=["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)
    return df
