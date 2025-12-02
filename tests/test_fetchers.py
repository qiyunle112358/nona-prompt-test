"""
论文信息获取器测试
使用3个已知论文测试
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# 测试用的已知论文（这些是真实存在的论文）
TEST_PAPERS = [
    {
        'title': 'Attention Is All You Need',
        'expected_arxiv_id': '1706.03762'
    },
    {
        'title': 'BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding',
        'expected_arxiv_id': '1810.04805'
    },
    {
        'title': 'Language Models are Few-Shot Learners',
        'expected_arxiv_id': '2005.14165'
    }
]


def test_fetchers():
    """测试论文信息获取器"""
    logger.info("="*60)
    logger.info("测试：论文信息获取器")
    logger.info("="*60)
    logger.info("使用3个已知论文测试")
    logger.info("="*60)
    
    try:
        from fetchers import fetch_paper_info
        
        success_count = 0
        
        for i, test_paper in enumerate(TEST_PAPERS, 1):
            logger.info(f"\n[测试{i}] {test_paper['title']}")
            logger.info("-"*60)
            
            try:
                # 获取论文信息
                info = fetch_paper_info(test_paper['title'])
                
                if info:
                    # 验证返回的字段
                    assert 'title' in info, "缺少title字段"
                    assert 'arxiv_id' in info, "缺少arxiv_id字段"
                    assert 'pdf_url' in info, "缺少pdf_url字段"
                    assert 'authors' in info, "缺少authors字段"
                    
                    logger.info(f"✓ 成功获取论文信息")
                    logger.info(f"  标题: {info['title'][:60]}...")
                    logger.info(f"  arXiv ID: {info.get('arxiv_id', 'N/A')}")
                    logger.info(f"  PDF URL: {info.get('pdf_url', 'N/A')[:50]}...")
                    logger.info(f"  作者数: {len(info.get('authors', []))}")
                    if info.get('authors'):
                        logger.info(f"  首作者: {info['authors'][0]}")
                    
                    # 验证arXiv ID（如果指定了预期值）
                    if 'expected_arxiv_id' in test_paper:
                        if info.get('arxiv_id') == test_paper['expected_arxiv_id']:
                            logger.info(f"  ✓ arXiv ID匹配: {info['arxiv_id']}")
                        else:
                            logger.warning(f"  ⚠ arXiv ID不匹配: 期望{test_paper['expected_arxiv_id']}, 实际{info.get('arxiv_id')}")
                    
                    success_count += 1
                else:
                    logger.warning(f"✗ 未找到论文信息")
                
            except Exception as e:
                logger.error(f"✗ 获取失败: {e}")
                continue
        
        logger.info("\n" + "="*60)
        logger.info(f"测试结果: {success_count}/{len(TEST_PAPERS)} 成功")
        
        if success_count >= 2:
            logger.info("✓ 论文信息获取器测试通过")
            logger.info("="*60)
            return True
        else:
            logger.error("✗ 成功率过低，测试失败")
            logger.info("="*60)
            return False
        
    except Exception as e:
        logger.error(f"\n✗ 论文信息获取器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_fetch():
    """测试批量获取"""
    logger.info("\n[额外测试] 批量获取")
    logger.info("-"*60)
    
    try:
        from fetchers import batch_fetch_papers
        
        papers = [{'title': p['title']} for p in TEST_PAPERS]
        
        results = batch_fetch_papers(papers, show_progress=True)
        
        logger.info(f"✓ 批量获取完成: {len(results)}/{len(papers)} 成功")
        return True
        
    except Exception as e:
        logger.error(f"✗ 批量获取失败: {e}")
        return False


if __name__ == "__main__":
    success = test_fetchers()
    
    if success:
        # 如果基础测试通过，再测试批量功能
        test_batch_fetch()
    
    sys.exit(0 if success else 1)

