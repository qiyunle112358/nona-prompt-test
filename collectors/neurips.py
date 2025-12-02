"""
NeurIPS论文收集器
从NeurIPS会议网站收集论文标题
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import time

logger = logging.getLogger(__name__)


def collect_neurips_papers(year: int = 2024) -> List[Dict[str, str]]:
    """
    收集NeurIPS论文标题
    
    Args:
        year: 会议年份
        
    Returns:
        论文列表，每个元素包含 {title, url, source}
    """
    logger.info(f"Collecting NeurIPS {year} papers")
    
    papers = []
    
    try:
        # NeurIPS论文列表URL（根据年份调整）
        # 注意：这里提供多个可能的URL模式，实际使用时可能需要根据网站结构调整
        urls = [
            f"https://papers.nips.cc/paper_files/paper/{year}",
            f"https://proceedings.neurips.cc/paper/{year}",
            f"https://neurips.cc/virtual/{year}/papers.html"
        ]
        
        # 尝试不同的URL
        for base_url in urls:
            try:
                logger.info(f"Trying URL: {base_url}")
                response = requests.get(base_url, timeout=30)
                response.raise_for_status()
                
                # 解析HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 查找论文标题（根据网站结构调整选择器）
                # 方法1：查找论文链接
                paper_links = soup.find_all('a', href=lambda x: x and '/paper/' in x)
                
                for link in paper_links:
                    title = link.get_text(strip=True)
                    if title and len(title) > 10:  # 过滤太短的标题
                        papers.append({
                            'title': title,
                            'url': link.get('href', ''),
                            'source': f'NeurIPS{year}'
                        })
                
                if papers:
                    logger.info(f"Successfully collected {len(papers)} papers from {base_url}")
                    break
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Failed to access {base_url}: {e}")
                continue
        
        if not papers:
            logger.warning(f"Could not collect papers from any URL. May need to update URL patterns.")
            logger.info(f"Manual collection recommended: Visit https://neurips.cc/Conferences/{year}/Schedule")
        
        # 去重
        papers = _deduplicate_papers(papers)
        
        logger.info(f"Successfully collected {len(papers)} papers from NeurIPS {year}")
        return papers
        
    except Exception as e:
        logger.error(f"Error collecting NeurIPS papers: {e}")
        return papers


def _deduplicate_papers(papers: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """去重论文列表"""
    seen_titles = set()
    unique_papers = []
    
    for paper in papers:
        title_lower = paper['title'].lower().strip()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            unique_papers.append(paper)
    
    return unique_papers

