from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path: Path | str) -> list[dict[str, Any]]:
    """Tao bo evaluation set gom 10 cau hoi qua 4 nhom nghiep vu tu cleaned dataframe.

    Cac loai cau hoi:
    - summary: Hoi tom tat noi dung
    - authors: Hoi danh sach tac gia
    - date: Hoi ngay xuat ban
    - categories: Hoi linh vuc/chu de
    """
    if len(df) < 5:
        raise ValueError(f"Dataframe phai co it nhat 5 bai bao, hien tai co {len(df)}")

    # Chon 10 bai bao (hoac lap vong neu it hon 10)
    papers = df.to_dict(orient="records")
    target_count = 10
    selected_papers = [papers[i % len(papers)] for i in range(target_count)]

    # Phan bo 4 nhom: 3 summary, 3 authors, 2 date, 2 categories
    question_types = [
        "summary",
        "authors",
        "date",
        "categories",
        "summary",
        "authors",
        "date",
        "categories",
        "summary",
        "authors",
    ]

    test_set: list[dict[str, Any]] = []
    for idx, (paper, q_type) in enumerate(zip(selected_papers, question_types, strict=False), start=1):
        title = paper["title"]
        pid = paper["paper_id"]

        if q_type == "summary":
            question = f"What is the summary of '{title}'?"
            ground_truth = first_sentence(paper["summary"])
        elif q_type == "authors":
            question = f"Who authored '{title}'?"
            ground_truth = str(paper["authors_joined"])
        elif q_type == "date":
            question = f"When was '{title}' published?"
            ground_truth = str(paper["published"])
        elif q_type == "categories":
            question = f"What categories does '{title}' belong to?"
            ground_truth = str(paper["categories_joined"])
        else:
            question = f"What is the summary of '{title}'?"
            ground_truth = first_sentence(paper["summary"])

        test_set.append(
            {
                "id": f"q_{idx:02d}",
                "question_type": q_type,
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [pid],
            }
        )

    out_p = Path(output_path)
    write_json(out_p, test_set)
    return test_set
