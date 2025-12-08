"""
论文信息获取模块
根据论文标题获取详细信息（arXiv ID、PDF URL、作者、摘要等）
"""

from .paper_fetcher import fetch_paper_info, batch_fetch_papers, RateLimitError

__all__ = ['fetch_paper_info', 'batch_fetch_papers', 'RateLimitError']

