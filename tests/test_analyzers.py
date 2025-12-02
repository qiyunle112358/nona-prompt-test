"""
AI分析器测试
使用短文本测试分析功能
注意：会产生少量API费用（约$0.01-0.02）
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# 测试用的样本文本（简短，减少API费用）
SAMPLE_TEXT_RELEVANT = """
Title: Deep Reinforcement Learning for Robotic Grasping

Abstract: This paper presents a novel approach to robotic grasping using deep reinforcement 
learning. We propose a method that enables robots to learn grasping strategies from raw visual 
inputs without manual feature engineering.

Introduction: Robotic manipulation and grasping remain challenging problems in robotics. 
Traditional approaches rely on analytical grasp planning, which requires precise object models 
and calibrated sensors. In contrast, our learning-based approach...

Methods: We use a deep Q-network (DQN) to learn a grasping policy. The robot receives RGB-D 
images as input and outputs motor commands for the gripper. The reward function is designed 
to encourage successful grasps while penalizing collisions.

Results: Our method achieves 92% success rate on a dataset of 100 household objects, 
outperforming the baseline by 15%. The learned policy generalizes well to novel objects.
"""

SAMPLE_TEXT_IRRELEVANT = """
Title: Natural Language Processing for Medical Diagnosis

Abstract: This paper explores the application of transformer models to automated medical 
diagnosis from patient records. We demonstrate that large language models can extract 
relevant symptoms and suggest possible diagnoses.

Introduction: Electronic health records (EHRs) contain vast amounts of unstructured text 
data. Extracting actionable insights from this data is crucial for improving healthcare 
outcomes. Our work focuses on using NLP to assist physicians...

Methods: We fine-tune BERT on a dataset of 50,000 medical records. The model is trained 
to identify symptoms, predict diagnoses, and suggest treatments based on historical data.

Results: Our approach achieves 85% accuracy on diagnosis prediction, matching or exceeding 
human physician performance in several categories.
"""


def test_analyzers(provider: str = "openai"):
    """测试AI分析器"""
    logger.info("="*60)
    logger.info("测试：AI分析器")
    logger.info("="*60)
    logger.info(f"LLM提供商: {provider}")
    logger.info("注意：此测试会产生少量API费用（约$0.01-0.02）")
    logger.info("="*60)
    
    # 检查API配置
    try:
        from config import get_api_key
        api_key = get_api_key(provider)
        
        if not api_key or api_key == '':
            logger.error(f"✗ {provider.upper()} API密钥未配置")
            logger.error("请在.env文件中配置API密钥")
            return False
        
        logger.info(f"✓ API密钥已配置 (长度: {len(api_key)})")
        
    except Exception as e:
        logger.error(f"✗ 配置错误: {e}")
        return False
    
    try:
        from analyzers import analyze_paper
        from config import RELEVANCE_TAGS
        
        # 测试1: 分析相关论文
        logger.info("\n[测试1] 分析相关论文")
        logger.info(f"相关性标签: {', '.join(RELEVANCE_TAGS[:5])}...")
        logger.info("-"*60)
        
        paper_info_1 = {
            'title': 'Deep Reinforcement Learning for Robotic Grasping',
            'authors': ['Test Author A', 'Test Author B'],
            'abstract': 'A paper about robotic grasping using deep learning.'
        }
        
        result1 = analyze_paper(
            paper_text=SAMPLE_TEXT_RELEVANT,
            paper_info=paper_info_1,
            provider=provider,
            relevance_tags=RELEVANCE_TAGS
        )
        
        assert result1 is not None, "分析返回None"
        assert 'is_relevant' in result1, "缺少is_relevant字段"
        assert 'relevance_score' in result1, "缺少relevance_score字段"
        assert 'reasoning' in result1, "缺少reasoning字段"
        assert 'summary' in result1, "缺少summary字段"
        
        # 验证分数范围
        score1 = result1['relevance_score']
        assert 0 <= score1 <= 1, f"分数超出范围: {score1}"
        
        logger.info(f"✓ 分析完成")
        logger.info(f"  相关性: {'是' if result1['is_relevant'] else '否'}")
        logger.info(f"  分数: {score1:.2f}")
        logger.info(f"  理由: {result1['reasoning'][:100]}...")
        logger.info(f"  总结: {result1['summary'][:150]}...")
        
        # 验证结果合理性
        if score1 >= 0.7:
            logger.info("  ✓ 分数合理（应该是高相关性论文）")
        else:
            logger.warning(f"  ⚠ 分数偏低（期望>=0.7，实际{score1:.2f}）")
        
        # 测试2: 分析不相关论文
        logger.info("\n[测试2] 分析不相关论文")
        logger.info("-"*60)
        
        paper_info_2 = {
            'title': 'Natural Language Processing for Medical Diagnosis',
            'authors': ['Test Author C', 'Test Author D'],
            'abstract': 'A paper about NLP in healthcare.'
        }
        
        result2 = analyze_paper(
            paper_text=SAMPLE_TEXT_IRRELEVANT,
            paper_info=paper_info_2,
            provider=provider,
            relevance_tags=RELEVANCE_TAGS
        )
        
        assert result2 is not None, "分析返回None"
        
        score2 = result2['relevance_score']
        
        logger.info(f"✓ 分析完成")
        logger.info(f"  相关性: {'是' if result2['is_relevant'] else '否'}")
        logger.info(f"  分数: {score2:.2f}")
        logger.info(f"  理由: {result2['reasoning'][:100]}...")
        logger.info(f"  总结: {result2['summary'][:150]}...")
        
        # 验证结果合理性
        if score2 < 0.5:
            logger.info("  ✓ 分数合理（应该是低相关性论文）")
        else:
            logger.warning(f"  ⚠ 分数偏高（期望<0.5，实际{score2:.2f}）")
        
        # 测试3: 对比分析
        logger.info("\n[测试3] 对比分析")
        logger.info("-"*60)
        logger.info(f"相关论文分数: {score1:.2f}")
        logger.info(f"不相关论文分数: {score2:.2f}")
        logger.info(f"分数差异: {abs(score1 - score2):.2f}")
        
        if score1 > score2:
            logger.info("✓ 分数对比合理（相关>不相关）")
        else:
            logger.warning("⚠ 分数对比异常（相关<=不相关）")
        
        logger.info("\n" + "="*60)
        logger.info("✓ AI分析器测试通过")
        logger.info("="*60)
        logger.info("\n提示：")
        logger.info("- 如果分数不够准确，可以调整提示词")
        logger.info("- 不同的LLM模型可能有不同的表现")
        logger.info("- 此测试产生的API费用约$0.01-0.02")
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ AI分析器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--provider', type=str, choices=['openai', 'anthropic'], 
                       default='openai', help='LLM提供商')
    args = parser.parse_args()
    
    success = test_analyzers(args.provider)
    sys.exit(0 if success else 1)

