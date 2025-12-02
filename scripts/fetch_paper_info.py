"""
论文信息获取脚本
从数据库读取待处理的论文，获取详细信息
"""

import argparse
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_PATH, LOG_LEVEL, LOG_FORMAT
from database import Database
from fetchers import fetch_paper_info

# 配置日志
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='获取论文详细信息')
    parser.add_argument('--limit', type=int, default=None, help='处理数量限制')
    parser.add_argument('--status', type=str, default='pending', help='要处理的论文状态')
    
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("论文信息获取脚本")
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
    success_count = 0
    
    for i, paper in enumerate(papers, 1):
        paper_id = paper['id']
        title = paper['title']
        
        logger.info(f"[{i}/{len(papers)}] 处理: {title}")
        
        try:
            # 获取详细信息
            info = fetch_paper_info(title)
            
            if info:
                # 更新数据库
                updates = {
                    'arxiv_id': info.get('arxiv_id'),
                    'pdf_url': info.get('pdf_url'),
                    'authors': str(info.get('authors', [])),
                    'abstract': info.get('abstract'),
                    'published_date': info.get('published_date'),
                    'status': 'downloaded'
                }
                
                db.update_paper_info(paper_id, updates)
                success_count += 1
                logger.info(f"✓ 成功获取信息")
            else:
                logger.warning(f"✗ 未找到论文信息")
                
        except Exception as e:
            logger.error(f"✗ 处理失败: {e}")
            continue
    
    logger.info(f"\n{'='*80}")
    logger.info(f"处理完成: {success_count}/{len(papers)} 篇成功")
    logger.info(f"{'='*80}\n")
    
    # 显示统计信息
    stats = db.get_statistics()
    logger.info("数据库统计:")
    logger.info(f"总论文数: {stats['total_papers']}")
    logger.info(f"状态分布: {stats['status_counts']}")
    logger.info(f"{'='*80}\n")


if __name__ == '__main__':
    main()

