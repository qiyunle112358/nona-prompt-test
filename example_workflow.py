"""
完整工作流示例
展示如何使用Python API进行论文收集和分析
"""

import logging
from pathlib import Path

# 导入所有模块
from config import DB_PATH, PDF_DIR, TEXT_DIR, RELEVANCE_TAGS
from database import Database
import collectors
from fetchers import fetch_paper_info
from processors import download_pdf, convert_pdf_to_text
from analyzers import analyze_paper

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_workflow():
    """完整工作流示例"""
    
    logger.info("="*80)
    logger.info("具身智能论文Survey工具 - 工作流示例")
    logger.info("="*80)
    
    # 初始化数据库
    db = Database(str(DB_PATH))
    
    # ========== 步骤1: 收集论文标题 ==========
    logger.info("\n步骤1: 收集论文标题")
    logger.info("-"*80)
    
    # 收集arXiv论文（限制10篇用于演示）
    papers = collectors.collect_arxiv_papers(year=2024, category="cs.RO", max_results=10)
    logger.info(f"收集到 {len(papers)} 篇论文")
    
    # 保存到数据库
    for paper in papers:
        db.insert_paper({
            'title': paper['title'],
            'source': paper['source'],
            'published_date': paper.get('published_date', ''),
            'status': 'pendingTitles'
        })
    
    # ========== 步骤2: 获取论文详细信息 ==========
    logger.info("\n步骤2: 获取论文详细信息")
    logger.info("-"*80)
    
    # 获取待处理的论文
    pending_papers = db.get_papers_by_status('pendingTitles', limit=5)
    
    for paper in pending_papers:
        logger.info(f"\n处理: {paper['title']}")
        
        # 获取详细信息
        info = fetch_paper_info(paper['title'])
        
        if info:
            # 更新数据库
            db.update_paper_info(paper['id'], {
                'arxiv_id': info.get('arxiv_id'),
                'pdf_url': info.get('pdf_url'),
                'authors': info.get('authors', []),
                'abstract': info.get('abstract'),
                'status': 'TobeDownloaded'
            })
            db.remove_detail_failure(paper['id'])
            logger.info("✓ 成功获取信息")
        else:
            logger.warning("✗ 未找到论文信息")
            db.update_paper_status(paper['id'], 'detailFailed')
            db.record_detail_failure(paper['id'], paper['title'], paper.get('source'), "示例流程未找到")
    
    # ========== 步骤3: 下载和处理PDF ==========
    logger.info("\n步骤3: 下载和处理PDF")
    logger.info("-"*80)
    
    # 获取已下载信息的论文
    downloaded_papers = db.get_papers_by_status('TobeDownloaded', limit=3)
    
    for paper in downloaded_papers:
        arxiv_id = paper.get('arxiv_id')
        pdf_url = paper.get('pdf_url')
        
        if not arxiv_id or not pdf_url:
            continue
        
        logger.info(f"\n处理: {paper['title']}")
        
        # 下载PDF
        pdf_path = PDF_DIR / f"{arxiv_id}.pdf"
        if download_pdf(pdf_url, pdf_path):
            logger.info("✓ PDF下载成功")
            db.remove_download_failure(paper['id'])
            
            # 转换为文本
            text_path = TEXT_DIR / f"{arxiv_id}.txt"
            if convert_pdf_to_text(pdf_path, text_path):
                logger.info("✓ 文本转换成功")
                
                # 更新状态
                db.update_paper_status(paper['id'], 'processed')
            else:
                logger.warning("✗ 文本转换失败")
        else:
            logger.warning("✗ PDF下载失败")
            db.update_paper_status(paper['id'], 'downloadFailed')
            db.record_download_failure(paper['id'], paper['title'], arxiv_id, pdf_url, "示例流程下载失败")
    
    # ========== 步骤4: AI分析和筛选 ==========
    logger.info("\n步骤4: AI分析和筛选")
    logger.info("-"*80)
    
    # 获取已处理的论文
    processed_papers = db.get_papers_by_status('processed', limit=2)
    
    for paper in processed_papers:
        arxiv_id = paper.get('arxiv_id')
        
        if not arxiv_id:
            continue
        
        logger.info(f"\n分析: {paper['title']}")
        
        # 读取文本
        text_path = TEXT_DIR / f"{arxiv_id}.txt"
        if not text_path.exists():
            continue
        
        with open(text_path, 'r', encoding='utf-8') as f:
            paper_text = f.read()
        
        # 分析论文
        result = analyze_paper(
            paper_text=paper_text[:20000],  # 限制长度用于演示
            paper_info=paper,
            provider='openai',
            relevance_tags=RELEVANCE_TAGS
        )
        
        if result:
            # 保存分析结果
            result['paper_id'] = paper['id']
            db.insert_analysis_result(result)
            
            # 更新状态
            db.update_paper_status(paper['id'], 'analyzed')
            
            logger.info(f"✓ 分析完成")
            logger.info(f"  相关性: {'是' if result['is_relevant'] else '否'}")
            logger.info(f"  分数: {result['relevance_score']:.2f}")
            logger.info(f"  理由: {result['reasoning'][:100]}...")
        else:
            logger.warning("✗ 分析失败")
    
    # ========== 显示统计信息 ==========
    logger.info("\n" + "="*80)
    logger.info("统计信息")
    logger.info("="*80)
    
    stats = db.get_statistics()
    logger.info(f"总论文数: {stats['total_papers']}")
    logger.info(f"已分析: {stats['analyzed_papers']}")
    logger.info(f"相关论文: {stats['relevant_papers']}")
    logger.info(f"状态分布: {stats['status_counts']}")
    
    # 显示相关论文
    relevant_papers = db.get_relevant_papers(min_score=0.5)
    
    if relevant_papers:
        logger.info(f"\n相关论文列表 (共{len(relevant_papers)}篇):")
        logger.info("-"*80)
        
        for i, p in enumerate(relevant_papers, 1):
            logger.info(f"\n{i}. {p['title']}")
            logger.info(f"   分数: {p.get('relevance_score', 0):.2f}")
            logger.info(f"   理由: {p.get('reasoning', 'N/A')[:100]}...")
    
    logger.info("\n" + "="*80)
    logger.info("工作流完成！")
    logger.info("="*80)


if __name__ == '__main__':
    # 注意：运行此示例前，请确保已配置.env文件中的API密钥
    
    # 检查是否配置了API密钥
    from config import get_api_key
    
    try:
        api_key = get_api_key('openai')
        if not api_key or api_key == '':
            logger.error("请先在.env文件中配置OPENAI_API_KEY")
            logger.error("参考env.example文件进行配置")
            exit(1)
    except Exception as e:
        logger.error(f"配置错误: {e}")
        exit(1)
    
    # 运行示例工作流
    example_workflow()

