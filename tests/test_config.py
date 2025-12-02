"""
配置模块测试
验证配置文件加载和环境变量读取
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_config():
    """测试配置模块"""
    logger.info("="*60)
    logger.info("测试：配置模块")
    logger.info("="*60)
    
    try:
        from config import (
            PROJECT_ROOT, DATA_DIR, PDF_DIR, TEXT_DIR, DB_PATH,
            RELEVANCE_TAGS, get_api_key, get_model_name
        )
        
        # 测试1: 路径配置
        logger.info("\n[测试1] 路径配置")
        assert PROJECT_ROOT.exists(), "项目根目录不存在"
        logger.info(f"✓ 项目根目录: {PROJECT_ROOT}")
        
        # 测试2: 数据目录创建
        logger.info("\n[测试2] 数据目录")
        assert DATA_DIR.exists(), "数据目录未创建"
        assert PDF_DIR.exists(), "PDF目录未创建"
        assert TEXT_DIR.exists(), "文本目录未创建"
        logger.info(f"✓ 数据目录: {DATA_DIR}")
        logger.info(f"✓ PDF目录: {PDF_DIR}")
        logger.info(f"✓ 文本目录: {TEXT_DIR}")
        
        # 测试3: 相关性标签
        logger.info("\n[测试3] 相关性标签")
        assert len(RELEVANCE_TAGS) > 0, "相关性标签为空"
        logger.info(f"✓ 相关性标签数量: {len(RELEVANCE_TAGS)}")
        logger.info(f"  标签: {', '.join(RELEVANCE_TAGS[:5])}...")
        
        # 测试4: API配置
        logger.info("\n[测试4] API配置")
        try:
            openai_key = get_api_key("openai")
            if openai_key:
                logger.info(f"✓ OpenAI API密钥已配置 (长度: {len(openai_key)})")
            else:
                logger.warning("⚠ OpenAI API密钥未配置")
        except Exception as e:
            logger.warning(f"⚠ 无法读取OpenAI API密钥: {e}")
        
        try:
            model = get_model_name("openai")
            logger.info(f"✓ 默认OpenAI模型: {model}")
        except Exception as e:
            logger.error(f"✗ 无法读取模型配置: {e}")
        
        logger.info("\n" + "="*60)
        logger.info("✓ 配置模块测试通过")
        logger.info("="*60)
        return True
        
    except Exception as e:
        logger.error(f"\n✗ 配置模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_config()
    sys.exit(0 if success else 1)

