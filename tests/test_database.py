"""
数据库模块测试
验证数据库CRUD操作
"""

import sys
from pathlib import Path
import tempfile
import os

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_database():
    """测试数据库模块"""
    logger.info("="*60)
    logger.info("测试：数据库模块")
    logger.info("="*60)
    
    # 使用临时数据库
    temp_dir = Path(__file__).parent / "temp"
    temp_dir.mkdir(exist_ok=True)
    test_db_path = temp_dir / "test_papers.db"
    
    # 删除旧的测试数据库
    if test_db_path.exists():
        test_db_path.unlink()
    
    try:
        from database import Database
        
        # 测试1: 数据库初始化
        logger.info("\n[测试1] 数据库初始化")
        db = Database(str(test_db_path))
        assert test_db_path.exists(), "数据库文件未创建"
        logger.info("✓ 数据库创建成功")
        
        # 测试2: 插入论文
        logger.info("\n[测试2] 插入论文")
        paper1 = {
            'title': '测试论文1: Deep Learning for Robotics',
            'arxiv_id': '2024.12345',
            'pdf_url': 'https://arxiv.org/pdf/2024.12345.pdf',
            'authors': ['Author A', 'Author B'],
            'abstract': 'This is a test paper about deep learning.',
            'published_date': '2024-01-01',
            'source': 'arXiv2024',
            'status': 'pending'
        }
        
        result = db.insert_paper(paper1)
        assert result, "插入论文失败"
        logger.info("✓ 论文插入成功")
        
        # 测试3: 查询论文
        logger.info("\n[测试3] 查询论文")
        retrieved = db.get_paper_by_id('2024.12345')
        assert retrieved is not None, "查询论文失败"
        assert retrieved['title'] == paper1['title'], "标题不匹配"
        logger.info(f"✓ 论文查询成功: {retrieved['title']}")
        
        # 测试4: 批量插入
        logger.info("\n[测试4] 批量插入")
        papers = [
            {
                'title': f'测试论文{i}: Test Paper {i}',
                'source': 'NeurIPS2024',
                'status': 'pending'
            }
            for i in range(2, 5)
        ]
        count = db.batch_insert_papers(papers)
        assert count == 3, f"应插入3篇，实际插入{count}篇"
        logger.info(f"✓ 批量插入成功: {count}篇")
        
        # 测试5: 按状态查询
        logger.info("\n[测试5] 按状态查询")
        pending_papers = db.get_papers_by_status('pending')
        assert len(pending_papers) >= 3, "查询结果数量不正确"
        logger.info(f"✓ 状态查询成功: 找到{len(pending_papers)}篇待处理论文")
        
        # 测试6: 更新状态
        logger.info("\n[测试6] 更新论文状态")
        result = db.update_paper_status('2024.12345', 'downloaded')
        assert result, "更新状态失败"
        
        updated = db.get_paper_by_id('2024.12345')
        assert updated['status'] == 'downloaded', "状态未更新"
        logger.info("✓ 状态更新成功")
        
        # 测试7: 更新论文信息
        logger.info("\n[测试7] 更新论文信息")
        updates = {
            'abstract': 'Updated abstract',
            'status': 'processed'
        }
        result = db.update_paper_info('2024.12345', updates)
        assert result, "更新信息失败"
        logger.info("✓ 论文信息更新成功")
        
        # 测试8: 插入分析结果
        logger.info("\n[测试8] 插入分析结果")
        analysis = {
            'paper_id': '2024.12345',
            'is_relevant': 1,
            'relevance_score': 0.85,
            'reasoning': '这篇论文高度相关',
            'summary': '论文总结...'
        }
        result = db.insert_analysis_result(analysis)
        assert result, "插入分析结果失败"
        logger.info("✓ 分析结果插入成功")
        
        # 测试9: 查询分析结果
        logger.info("\n[测试9] 查询分析结果")
        analysis_result = db.get_analysis_result('2024.12345')
        assert analysis_result is not None, "查询分析结果失败"
        assert analysis_result['relevance_score'] == 0.85, "分数不匹配"
        logger.info(f"✓ 分析结果查询成功: 分数={analysis_result['relevance_score']}")
        
        # 测试10: 查询相关论文
        logger.info("\n[测试10] 查询相关论文")
        relevant_papers = db.get_relevant_papers(min_score=0.5)
        assert len(relevant_papers) >= 1, "应至少有1篇相关论文"
        logger.info(f"✓ 相关论文查询成功: {len(relevant_papers)}篇")
        
        # 测试11: 统计信息
        logger.info("\n[测试11] 统计信息")
        stats = db.get_statistics()
        assert stats['total_papers'] >= 4, "论文总数不正确"
        assert stats['analyzed_papers'] >= 1, "已分析数量不正确"
        assert stats['relevant_papers'] >= 1, "相关论文数量不正确"
        logger.info(f"✓ 统计信息:")
        logger.info(f"  总论文数: {stats['total_papers']}")
        logger.info(f"  已分析: {stats['analyzed_papers']}")
        logger.info(f"  相关论文: {stats['relevant_papers']}")
        
        logger.info("\n" + "="*60)
        logger.info("✓ 数据库模块测试通过")
        logger.info("="*60)
        return True
        
    except Exception as e:
        logger.error(f"\n✗ 数据库模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理测试数据库
        if test_db_path.exists():
            logger.info(f"\n清理测试数据库: {test_db_path}")
            # test_db_path.unlink()  # 保留用于检查


if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)

