"""
测试LLM配置是否正确
用于验证API密钥和连接是否正常
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    DEFAULT_LLM_PROVIDER,
    get_api_key,
    get_model_name,
    get_base_url
)
from llm_client import test_connection
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_llm_config():
    """测试LLM配置"""
    
    logger.info("="*80)
    logger.info("LLM配置测试")
    logger.info("="*80)
    
    # 显示当前配置
    logger.info(f"\n当前配置的LLM提供商: {DEFAULT_LLM_PROVIDER}")
    
    try:
        api_key = get_api_key()
        model = get_model_name()
        base_url = get_base_url()
        
        logger.info(f"API密钥: {'已配置 (' + api_key[:10] + '...)' if api_key else '未配置 ❌'}")
        logger.info(f"模型名称: {model if model else '未配置 ❌'}")
        logger.info(f"Base URL: {base_url if base_url else '未配置 ❌'}")
        
        if not api_key:
            logger.error("\n❌ 错误：API密钥未配置！")
            logger.info("\n请在 .env 文件中配置以下参数：")
            logger.info(f"  DEFAULT_LLM_PROVIDER={DEFAULT_LLM_PROVIDER}")
            if DEFAULT_LLM_PROVIDER == "custom":
                logger.info("  LLM_API_KEY=your-api-key-here")
                logger.info("  LLM_BASE_URL=https://api.deepseek.com/v1  # 或其他服务")
                logger.info("  LLM_MODEL=deepseek-chat  # 或其他模型")
            elif DEFAULT_LLM_PROVIDER == "openai":
                logger.info("  OPENAI_API_KEY=sk-your-key-here")
                logger.info("  OPENAI_BASE_URL=https://api.openai.com/v1")
                logger.info("  DEFAULT_OPENAI_MODEL=gpt-4o-mini")
            return False
        
        if not base_url:
            logger.error("\n❌ 错误：Base URL未配置！")
            logger.info("\n请在 .env 文件中配置 LLM_BASE_URL 或 OPENAI_BASE_URL")
            return False
        
        if not model:
            logger.error("\n❌ 错误：模型名称未配置！")
            logger.info("\n请在 .env 文件中配置 LLM_MODEL 或 DEFAULT_OPENAI_MODEL")
            return False
        
        logger.info("\n✓ 配置检查通过！")
        
        # 尝试调用API
        logger.info("\n正在测试API连接...")
        logger.info(f"请求地址: {base_url}")
        logger.info(f"使用模型: {model}")
        
        success = test_connection(
            base_url=base_url,
            api_key=api_key,
            model=model
        )
        
        if success:
            logger.info("\n✓ API连接测试成功！")
            return True
        else:
            logger.error("\n❌ API连接测试失败！")
            logger.info("\n可能的原因：")
            logger.info("  1. API密钥无效")
            logger.info("  2. Base URL错误")
            logger.info("  3. 模型名称错误")
            logger.info("  4. 网络连接问题")
            logger.info("  5. API服务暂时不可用")
            return False
            
    except Exception as e:
        logger.error(f"\n❌ 配置错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == '__main__':
    logger.info("\n这个脚本将测试你的LLM API配置是否正确\n")
    
    success = test_llm_config()
    
    logger.info("\n" + "="*80)
    if success:
        logger.info("✓ 配置测试通过！可以开始使用了。")
        logger.info("\n下一步：运行以下命令开始收集和分析论文")
        logger.info("  python scripts/collect_titles.py --source arxiv --year 2025")
        logger.info("  python scripts/fetch_paper_info.py --limit 10")
        logger.info("  python scripts/process_pdfs.py --limit 5")
        logger.info("  python scripts/analyze_papers.py --limit 5")
    else:
        logger.info("❌ 配置测试失败！请检查上述错误信息。")
        logger.info("\n参考文档：")
        logger.info("  - README.md")
        logger.info("  - env.example")
    logger.info("="*80 + "\n")
    
    sys.exit(0 if success else 1)

