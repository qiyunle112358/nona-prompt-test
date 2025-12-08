"""
将 downloadFailed 状态的论文重新放回 pendingTitles 队列
- 可选择清理已获取的详细信息
- 可选择删除已下载的PDF/TXT残留
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_PATH, PDF_DIR, TEXT_DIR, LOG_LEVEL, LOG_FORMAT
from database import Database

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def _file_id(paper):
    return paper.get("arxiv_id") or paper.get("id") or str(hash(paper.get("title", "")))


def _delete_files(file_id: str) -> None:
    for path in [PDF_DIR / f"{file_id}.pdf", TEXT_DIR / f"{file_id}.txt"]:
        if path.exists():
            path.unlink()
            logger.info("删除文件: %s", path)


def main():
    parser = argparse.ArgumentParser(description="重置 downloadFailed 条目")
    parser.add_argument("--limit", type=int, help="限制处理的数量")
    parser.add_argument("--delete-files", action="store_true", help="删除对应PDF/TXT文件")
    parser.add_argument("--clear-info", action="store_true", help="清空详细信息以重新获取")

    args = parser.parse_args()

    db = Database(str(DB_PATH))
    failures = db.get_papers_by_status("downloadFailed", args.limit)

    if not failures:
        logger.info("没有 downloadFailed 条目需要处理")
        return

    for paper in failures:
        logger.info("重置: %s", paper["title"])
        updates = {"status": "pendingTitles"}
        if args.clear_info:
            updates.update(
                {
                    "arxiv_id": None,
                    "pdf_url": None,
                    "authors": [],
                    "abstract": None,
                    "published_date": None,
                }
            )
        db.update_paper_info(paper["id"], updates)
        db.remove_download_failure(paper["id"])
        db.remove_detail_failure(paper["id"])

        if args.delete_files:
            _delete_files(_file_id(paper))

    logger.info("✓ 已重置 %d 条 downloadFailed 记录为 pendingTitles", len(failures))


if __name__ == "__main__":
    main()

