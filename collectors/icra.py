"""
ICRA论文收集器
从ICRA (International Conference on Robotics and Automation) 会议网站收集论文标题
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

logger = logging.getLogger(__name__)


def collect_icra_papers(year: int = 2024) -> List[Dict[str, str]]:
    """
    收集ICRA论文标题
    
    Args:
        year: 会议年份
        
    Returns:
        论文列表，每个元素包含 {title, url, source}
    """
    logger.info(f"Collecting ICRA {year} papers")
    
    papers = []
    
    try:
        # ICRA论文通常在IEEE Xplore上
        # 但直接爬取可能受限，建议使用API或手动下载
        
        # 尝试访问ICRA官方网站
        urls_to_try = [
            f"https://www.icra{year}.org/program/accepted-papers",
            f"https://www.icra{year}.org/accepted-papers",
        ]
        
        for url in urls_to_try:
            try:
                logger.info(f"Trying URL: {url}")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # 解析HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 查找论文标题
                paper_items = soup.find_all(['div', 'li', 'p'], class_=lambda x: x and ('paper' in x.lower() or 'title' in x.lower()))
                
                if not paper_items:
                    # 尝试查找所有可能是论文标题的元素
                    paper_items = soup.find_all('h3') + soup.find_all('h4')
                
                for item in paper_items:
                    try:
                        title = item.get_text(strip=True)
                        
                        if title and len(title) > 10 and len(title) < 500:
                            papers.append({
                                'title': title,
                                'url': url,
                                'source': f'ICRA{year}'
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
            logger.warning(f"Could not collect papers from ICRA {year} website.")
            logger.info(f"Manual collection recommended: Visit https://www.icra{year}.org/")
            logger.info(f"Or use IEEE Xplore: https://ieeexplore.ieee.org/xpl/conhome/{year}ICRA/proceeding")
        
        logger.info(f"Successfully collected {len(papers)} papers from ICRA {year}")
        return papers
        
    except Exception as e:
        logger.error(f"Error collecting ICRA papers: {e}")
        return papers

