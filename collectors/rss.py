"""
RSS论文收集器
从RSS (Robotics: Science and Systems) 会议网站收集论文标题
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

logger = logging.getLogger(__name__)


def collect_rss_papers(year: int = 2024) -> List[Dict[str, str]]:
    """
    收集RSS论文标题
    
    Args:
        year: 会议年份
        
    Returns:
        论文列表，每个元素包含 {title, url, source}
    """
    logger.info(f"Collecting RSS {year} papers")
    
    papers = []
    
    try:
        # RSS论文列表URL
        base_url = f"https://roboticsconference.org/program/papers/"
        
        # 尝试访问特定年份的页面
        urls_to_try = [
            f"https://roboticsconference.org/{year}/program/papers/",
            f"https://roboticsconference.org/program/papers/{year}/",
            base_url
        ]
        
        for url in urls_to_try:
            try:
                logger.info(f"Trying URL: {url}")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # 解析HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 查找论文标题
                # RSS网站结构可能需要调整
                paper_items = soup.find_all(['div', 'li'], class_=lambda x: x and ('paper' in x.lower() or 'title' in x.lower()))
                
                if not paper_items:
                    # 尝试其他模式
                    paper_items = soup.find_all('a', href=lambda x: x and 'paper' in x.lower())
                
                for item in paper_items:
                    try:
                        # 提取标题
                        title = item.get_text(strip=True)
                        
                        # 提取链接
                        link = item.get('href', '') if item.name == 'a' else ''
                        if link and not link.startswith('http'):
                            link = f"https://roboticsconference.org{link}"
                        
                        if title and len(title) > 10:
                            papers.append({
                                'title': title,
                                'url': link,
                                'source': f'RSS{year}'
                            })
                    except Exception as e:
                        logger.warning(f"Error parsing paper item: {e}")
                        continue
                
                if papers:
                    logger.info(f"Successfully collected {len(papers)} papers from {url}")
                    break
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Failed to access {url}: {e}")
                continue
        
        if not papers:
            logger.warning(f"Could not collect papers. Manual collection recommended.")
            logger.info(f"Visit: https://roboticsconference.org/{year}/program/papers/")
        
        logger.info(f"Successfully collected {len(papers)} papers from RSS {year}")
        return papers
        
    except Exception as e:
        logger.error(f"Error collecting RSS papers: {e}")
        return papers

