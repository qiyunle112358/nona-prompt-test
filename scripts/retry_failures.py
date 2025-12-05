"""
失败记录回退脚本
用于将获取详细信息失败或PDF下载失败的论文重新加入待处理队列
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_PATH, LOG_LEVEL, LOG_FORMAT
from database import Database

# 配置日志
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def _retry_detail_failures(db: Database, limit: Optional[int]) -> int:
    failures = db.get_detail_failures(limit)
    if not failures:
        logger.info("没有需要重试的详细信息失败记录")
        return 0

    for failure in failures:
        paper_id = failure.get("paper_id")
        if not paper_id:
            continue
        db.update_paper_status(paper_id, "pendingTitles")
        db.remove_detail_failure(paper_id)
        logger.info("已重置论文《%s》到 pendingTitles", failure.get("title"))
    return len(failures)


def _retry_download_failures(db: Database, limit: Optional[int]) -> int:
    failures = db.get_download_failures(limit)
    if not failures:
        logger.info("没有需要重试的PDF下载失败记录")
        return 0

    for failure in failures:
        paper_id = failure.get("paper_id")
        if not paper_id:
            continue
        db.update_paper_status(paper_id, "TobeDownloaded")
        db.remove_download_failure(paper_id)
        logger.info("已重置论文《%s》到 TobeDownloaded", failure.get("title"))
    return len(failures)


def main():
    parser = argparse.ArgumentParser(description="重试失败的论文任务")
    parser.add_argument(
        "--type",
        choices=["detail", "download", "all"],
        default="all",
        help="重试的失败类型",
    )
    parser.add_argument("--limit", type=int, default=None, help="每种类型的重试数量限制")
    args = parser.parse_args()

    db = Database(str(DB_PATH))

    logger.info("=" * 80)
    logger.info("失败任务重试脚本")
    logger.info("=" * 80)

    detail_count = download_count = 0

    if args.type in ("detail", "all"):
        detail_count = _retry_detail_failures(db, args.limit)

    if args.type in ("download", "all"):
        download_count = _retry_download_failures(db, args.limit)

    logger.info("\n重试完成：")
    logger.info("  详情失败重置: %d 条", detail_count)
    logger.info("  下载失败重置: %d 条", download_count)


if __name__ == "__main__":
    main()

