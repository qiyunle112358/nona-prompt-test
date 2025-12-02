"""
论文收集器测试
只收集少量论文验证功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_collectors():
    """测试论文收集器"""
    logger.info("="*60)
    logger.info("测试：论文收集器")
    logger.info("="*60)
    logger.info("注意：只测试arXiv，每个来源收集最多3篇论文")
    logger.info("="*60)
    
    try:
        import collectors
        
        # 测试1: arXiv收集器
        logger.info("\n[测试1] arXiv收集器")
        logger.info("收集2024年cs.RO分类，最多3篇...")
        
        papers = collectors.collect_arxiv_papers(
            year=2024,
            category="cs.RO",
            max_results=3  # 只收集3篇
        )
        
        assert len(papers) > 0, "未收集到论文"
        logger.info(f"✓ 收集到 {len(papers)} 篇论文")
        
        # 验证数据格式
        logger.info("\n验证数据格式:")
        for i, paper in enumerate(papers[:2], 1):  # 只显示前2篇
            assert 'title' in paper, "缺少title字段"
            assert 'source' in paper, "缺少source字段"
            assert paper['source'] == 'arXiv2024', "source格式不正确"
            
            logger.info(f"\n  论文{i}:")
            logger.info(f"    标题: {paper['title'][:60]}...")
            logger.info(f"    来源: {paper['source']}")
            if 'url' in paper:
                logger.info(f"    URL: {paper['url'][:50]}...")
        
        logger.info("\n✓ arXiv收集器测试通过")
        
        # 测试2: 其他收集器（可选）
        logger.info("\n[测试2] 其他收集器（跳过，需手动测试）")
        logger.info("  提示：其他会议收集器可能需要手动验证网站可访问性")
        logger.info("  - NeurIPS: python tests/test_collectors.py --test neurips")
        logger.info("  - ICLR: python tests/test_collectors.py --test iclr")
        
        logger.info("\n" + "="*60)
        logger.info("✓ 论文收集器测试通过")
        logger.info("="*60)
        return True
        
    except Exception as e:
        logger.error(f"\n✗ 论文收集器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_specific_collector(collector_name: str):
    """测试特定的收集器"""
    import collectors
    
    logger.info(f"\n测试 {collector_name.upper()} 收集器...")
    
    try:
        if collector_name == 'neurips':
            papers = collectors.collect_neurips_papers(2024)
        elif collector_name == 'iclr':
            papers = collectors.collect_iclr_papers(2024)
        elif collector_name == 'icml':
            papers = collectors.collect_icml_papers(2024)
        elif collector_name == 'corl':
            papers = collectors.collect_corl_papers(2024)
        elif collector_name == 'rss':
            papers = collectors.collect_rss_papers(2024)
        elif collector_name == 'icra':
            papers = collectors.collect_icra_papers(2024)
        elif collector_name == 'iros':
            papers = collectors.collect_iros_papers(2024)
        else:
            logger.error(f"未知的收集器: {collector_name}")
            return False
        
        if papers:
            logger.info(f"✓ {collector_name.upper()}: 收集到 {len(papers)} 篇论文")
            if papers:
                logger.info(f"  示例: {papers[0]['title'][:60]}...")
        else:
            logger.warning(f"⚠ {collector_name.upper()}: 未收集到论文（可能需要检查网站）")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ {collector_name.upper()} 测试失败: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', type=str, help='测试特定收集器')
    args = parser.parse_args()
    
    if args.test:
        success = test_specific_collector(args.test)
    else:
        success = test_collectors()
    
    sys.exit(0 if success else 1)

