"""
AI分析和筛选模块
使用大语言模型判断论文相关性并生成总结
"""

from .relevance_filter import analyze_paper, batch_analyze_papers

__all__ = ['analyze_paper', 'batch_analyze_papers']

