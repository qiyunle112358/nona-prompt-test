"""
PDF处理脚本
下载PDF并转换为文本
"""

import argparse
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_PATH, PDF_DIR, TEXT_DIR, LOG_LEVEL, LOG_FORMAT
from database import Database
from processors import download_pdf, convert_pdf_to_text

# 配置日志
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='处理PDF文件')
    parser.add_argument('--limit', type=int, default=None, help='处理数量限制')
    parser.add_argument('--status', type=str, default='downloaded', help='要处理的论文状态')
    parser.add_argument('--skip-download', action='store_true', help='跳过下载，只进行文本转换')
    parser.add_argument('--skip-convert', action='store_true', help='跳过文本转换，只进行下载')
    
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("PDF处理脚本")
    logger.info("="*80)
    
    # 初始化数据库
    db = Database(str(DB_PATH))
    
    # 获取待处理的论文
    papers = db.get_papers_by_status(args.status, args.limit)
    
    if not papers:
        logger.info(f"没有状态为 '{args.status}' 的论文需要处理")
        return
    
    logger.info(f"找到 {len(papers)} 篇论文待处理\n")
    
    # 处理每篇论文
    download_success = 0
    convert_success = 0
    
    for i, paper in enumerate(papers, 1):
        paper_id = paper['id']
        title = paper['title']
        arxiv_id = paper.get('arxiv_id')
        pdf_url = paper.get('pdf_url')
        
        logger.info(f"[{i}/{len(papers)}] 处理: {title}")
        
        if not arxiv_id or not pdf_url:
            logger.warning(f"✗ 缺少arXiv ID或PDF URL")
            continue
        
        pdf_path = PDF_DIR / f"{arxiv_id}.pdf"
        text_path = TEXT_DIR / f"{arxiv_id}.txt"
        
        try:
            # 下载PDF
            if not args.skip_download:
                if download_pdf(pdf_url, pdf_path):
                    download_success += 1
                else:
                    logger.warning(f"✗ PDF下载失败")
                    continue
            
            # 转换为文本
            if not args.skip_convert:
                if convert_pdf_to_text(pdf_path, text_path):
                    convert_success += 1
                    
                    # 更新状态
                    db.update_paper_status(paper_id, 'processed')
                else:
                    logger.warning(f"✗ 文本转换失败")
                    
        except Exception as e:
            logger.error(f"✗ 处理失败: {e}")
            continue
    
    logger.info(f"\n{'='*80}")
    logger.info("处理完成:")
    if not args.skip_download:
        logger.info(f"  PDF下载: {download_success}/{len(papers)} 篇成功")
    if not args.skip_convert:
        logger.info(f"  文本转换: {convert_success}/{len(papers)} 篇成功")
    logger.info(f"{'='*80}\n")
    
    # 显示统计信息
    stats = db.get_statistics()
    logger.info("数据库统计:")
    logger.info(f"总论文数: {stats['total_papers']}")
    logger.info(f"状态分布: {stats['status_counts']}")
    logger.info(f"{'='*80}\n")


if __name__ == '__main__':
    main()

