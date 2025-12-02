"""
论文标题收集器模块
从各个会议和arXiv收集论文标题
"""

from .arxiv import collect_arxiv_papers
from .neurips import collect_neurips_papers
from .iclr import collect_iclr_papers
from .icml import collect_icml_papers
from .corl import collect_corl_papers
from .rss import collect_rss_papers
from .icra import collect_icra_papers
from .iros import collect_iros_papers

__all__ = [
    'collect_arxiv_papers',
    'collect_neurips_papers',
    'collect_iclr_papers',
    'collect_icml_papers',
    'collect_corl_papers',
    'collect_rss_papers',
    'collect_icra_papers',
    'collect_iros_papers'
]

