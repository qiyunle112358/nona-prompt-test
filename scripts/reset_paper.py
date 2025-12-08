"""
重置指定论文记录
选项：
1. 清除已获取的详细信息（arXiv ID、PDF URL、作者、摘要等）
2. 删除已下载的 PDF / TXT 文件
两种操作都会将论文状态重置为 pendingTitles，方便重新处理
"""

import argparse
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_PATH, PDF_DIR, TEXT_DIR, LOG_LEVEL, LOG_FORMAT
from database import Database

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def _resolve_file_id(paper: dict) -> str:
    return paper.get("arxiv_id") or paper.get("id") or str(hash(paper.get("title", "")))


def delete_files(file_id: str) -> None:
    pdf_path = PDF_DIR / f"{file_id}.pdf"
    text_path = TEXT_DIR / f"{file_id}.txt"

    for path in [pdf_path, text_path]:
        if path.exists():
            path.unlink()
            logger.info("已删除文件: %s", path)


def main():
    parser = argparse.ArgumentParser(description="重置指定论文记录")
    parser.add_argument("--paper-id", required=True, help="要重置的论文ID（papers表的主键）")
    parser.add_argument(
        "--clear-info",
        action="store_true",
        help="清除已获取的详细信息（arXiv ID、PDF URL、作者、摘要等）",
    )
    parser.add_argument(
        "--delete-files",
        action="store_true",
        help="删除已下载的PDF和TXT文件",
    )

    args = parser.parse_args()

    if not args.clear_info and not args.delete_files:
        parser.error("请至少指定 --clear-info 或 --delete-files 其中之一")

    db = Database(str(DB_PATH))
    paper = db.get_paper_by_id(args.paper_id)

    if not paper:
        logger.error("未找到ID为 %s 的论文记录", args.paper_id)
        return

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

    if updates:
        db.update_paper_info(args.paper_id, updates)

    if args.delete_files:
        delete_files(_resolve_file_id(paper))

    # 清理失败记录，确保能重新进入队列
    db.remove_detail_failure(args.paper_id)
    db.remove_download_failure(args.paper_id)

    logger.info("✓ 已将论文 %s 重置为 pendingTitles", paper["title"])


if __name__ == "__main__":
    main()

