from __future__ import annotations

from dataclasses import asdict, dataclass
import logging
from pathlib import Path
import re
import time
from typing import Any
import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_abstract(raw: str) -> str:
    cleaned = re.sub(r"<[^>]+>", "", raw)
    return normalize_whitespace(cleaned)


def _parse_date(item: dict[str, Any]) -> str:
    pub = item.get("published") or item.get("published-print") or item.get("published-online")
    if pub and isinstance(pub, dict) and "date-parts" in pub:
        parts = pub["date-parts"]
        if parts and isinstance(parts[0], list) and len(parts[0]) > 0:
            dp = parts[0]
            year = dp[0]
            month = dp[1] if len(dp) > 1 else 1
            day = dp[2] if len(dp) > 2 else 1
            return f"{year:04d}-{month:02d}-{day:02d}"
    created = item.get("created")
    if created and isinstance(created, dict) and "date-time" in created:
        return str(created["date-time"])[:10]
    return "1970-01-01"


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload thanh list PaperRecord."""
    items = payload.get("message", {}).get("items", [])
    records: list[PaperRecord] = []
    for item in items:
        paper_id = str(item.get("DOI", "")).strip()
        title_list = item.get("title", [])
        title = title_list[0].strip() if isinstance(title_list, list) and title_list else str(item.get("title", "")).strip()
        abstract_raw = item.get("abstract", "")
        summary = _clean_abstract(abstract_raw)

        authors: list[str] = []
        for author in item.get("author", []):
            given = author.get("given", "").strip()
            family = author.get("family", "").strip()
            full_name = f"{given} {family}".strip()
            if full_name:
                authors.append(full_name)

        categories: list[str] = [str(cat).strip() for cat in item.get("subject", []) if str(cat).strip()]
        primary_category = categories[0] if categories else "Unknown"
        published = _parse_date(item)
        updated = published
        abs_url = str(item.get("URL", f"https://doi.org/{paper_id}" if paper_id else "")).strip()
        pdf_url = abs_url
        comment = f"Crossref record {paper_id}"

        if not paper_id or not title:
            continue

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Goi source API, luu raw response, parse thanh records."""
    payload: dict[str, Any] | None = None
    if settings.refresh_source:
        url = "https://api.crossref.org/works"
        params = {
            "query": settings.source_query,
            "filter": settings.source_filter,
            "rows": settings.max_results,
        }
        headers = {"User-Agent": "DataObservabilityBot/1.0 (mailto:student@vinuni.edu.vn)"}
        for attempt in range(3):
            try:
                response = requests.get(url, params=params, headers=headers, timeout=10)
                if response.status_code == 200:
                    payload = response.json()
                    break
                elif response.status_code in {429, 503}:
                    time.sleep(1.0 * (attempt + 1))
            except Exception as exc:
                logger.warning(f"Error fetching Crossref API (attempt {attempt + 1}): {exc}")
                time.sleep(1.0 * (attempt + 1))

    if payload is None:
        if settings.paths.raw_api_response.exists():
            payload = read_json(settings.paths.raw_api_response)
        else:
            raise FileNotFoundError(f"Raw API response snapshot not found at {settings.paths.raw_api_response}")

    write_json(settings.paths.raw_api_response, payload)
    records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_records_json, [asdict(r) for r in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Doc JSON snapshot va map thanh `PaperRecord`."""
    data = read_json(path)
    return [PaperRecord(**item) for item in data]
