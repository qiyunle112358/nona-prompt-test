"""
批量重置已下载/已处理的论文：
- 删除PDF与TXT文件
- 清空详细信息字段
- 将状态重置为 pendingTitles
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Set

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_PATH, PDF_DIR, TEXT_DIR, LOG_LEVEL, LOG_FORMAT
from database import Database

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

DEFAULT_STATUSES = ["TobeDownloaded", "processed", "analyzed", "downloadFailed"]


def _file_id(paper: Dict) -> str:
    return paper.get("arxiv_id") or paper.get("id") or str(hash(paper.get("title", "")))


def _delete_artifacts(file_id: str) -> None:
    pdf_path = PDF_DIR / f"{file_id}.pdf"
    text_path = TEXT_DIR / f"{file_id}.txt"

    for path in [pdf_path, text_path]:
        if path.exists():
            path.unlink()
            logger.info("删除文件: %s", path)


def reset_paper(db: Database, paper: Dict, delete_files: bool) -> None:
    file_id = _file_id(paper)

    if delete_files:
        _delete_artifacts(file_id)

    db.update_paper_info(
        paper["id"],
        {
            "arxiv_id": None,
            "pdf_url": None,
            "authors": [],
            "abstract": None,
            "published_date": None,
            "status": "pendingTitles",
        },
    )
    db.remove_detail_failure(paper["id"])
    db.remove_download_failure(paper["id"])


def main():
    parser = argparse.ArgumentParser(description="批量重置已下载的论文")
    parser.add_argument(
        "--statuses",
        nargs="+",
        default=DEFAULT_STATUSES,
        help=f"需要重置的状态（默认: {', '.join(DEFAULT_STATUSES)}）",
    )
    parser.add_argument("--dry-run", action="store_true", help="仅预览将要处理的数量")
    parser.add_argument("--keep-files", action="store_true", help="保留PDF/TXT文件，不删除")

    args = parser.parse_args()

    db = Database(str(DB_PATH))
    seen: Set[str] = set()
    affected = 0

    for status in args.statuses:
        papers = db.get_papers_by_status(status)
        for paper in papers:
            paper_id = paper["id"]
            if paper_id in seen:
                continue
            seen.add(paper_id)
            affected += 1
            logger.info("准备重置论文: %s (status=%s)", paper["title"], status)

            if not args.dry_run:
                reset_paper(db, paper, delete_files=not args.keep_files)

    if args.dry_run:
        logger.info("DRY-RUN: 预计重置 %d 篇论文", affected)
    else:
        logger.info("✓ 已重置 %d 篇论文，全部回到 pendingTitles", affected)


if __name__ == "__main__":
    main()

