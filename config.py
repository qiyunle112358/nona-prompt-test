"""
配置管理模块
管理API密钥、路径和其他配置项
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
PDF_DIR = DATA_DIR / "pdfs"
TEXT_DIR = DATA_DIR / "texts"
DB_PATH = DATA_DIR / "papers.db"

# 创建必要的目录
DATA_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)
TEXT_DIR.mkdir(exist_ok=True)

# API密钥
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# LLM配置
DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "openai")  # openai 或 anthropic
DEFAULT_OPENAI_MODEL = os.getenv("DEFAULT_OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_ANTHROPIC_MODEL = os.getenv("DEFAULT_ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

# 相关性分析标签（可配置）
RELEVANCE_TAGS = [
    "机器人",
    "具身智能",
    "灵巧手",
    "抓取",
    "世界模型",
    "物理智能",
    "embodied ai",
    "dexterous manipulation",
    "grasping",
    "world model"
]

# 会议和年份配置
CONFERENCES = {
    "ai": ["neurips", "iclr", "icml"],
    "robotics": ["corl", "rss", "icra", "iros"]
}

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 请求配置
REQUEST_TIMEOUT = 30  # 秒
MAX_RETRIES = 3
RATE_LIMIT_DELAY = 1  # 秒

# PDF处理配置
MAX_PDF_SIZE_MB = 50  # 最大PDF大小（MB）
OCR_ENABLED = os.getenv("OCR_ENABLED", "true").lower() == "true"

def get_api_key(provider: str = None) -> str:
    """获取指定提供商的API密钥"""
    if provider is None:
        provider = DEFAULT_LLM_PROVIDER
    
    if provider == "openai":
        return OPENAI_API_KEY
    elif provider == "anthropic":
        return ANTHROPIC_API_KEY
    else:
        raise ValueError(f"Unknown provider: {provider}")

def get_model_name(provider: str = None) -> str:
    """获取指定提供商的默认模型名称"""
    if provider is None:
        provider = DEFAULT_LLM_PROVIDER
    
    if provider == "openai":
        return DEFAULT_OPENAI_MODEL
    elif provider == "anthropic":
        return DEFAULT_ANTHROPIC_MODEL
    else:
        raise ValueError(f"Unknown provider: {provider}")

