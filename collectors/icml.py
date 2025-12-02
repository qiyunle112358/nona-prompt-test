"""
ICML论文收集器
从ICML会议网站收集论文标题
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

logger = logging.getLogger(__name__)


def collect_icml_papers(year: int = 2024) -> List[Dict[str, str]]:
    """
    收集ICML论文标题
    
    Args:
        year: 会议年份
        
    Returns:
        论文列表，每个元素包含 {title, url, source}
    """
    logger.info(f"Collecting ICML {year} papers")
    
    papers = []
    
    try:
        # ICML使用PMLR (Proceedings of Machine Learning Research)
        # URL格式：https://proceedings.mlr.press/v{volume}/
        
        # ICML卷号映射（需要根据年份更新）
        volume_mapping = {
            2024: 235,  # ICML 2024
            2023: 202,  # ICML 2023
            2022: 162,  # ICML 2022
        }
        
        volume = volume_mapping.get(year)
        if not volume:
            logger.warning(f"Unknown volume for ICML {year}. Please update volume_mapping.")
            logger.info(f"Manual collection recommended: Visit https://icml.cc/{year}/Conferences/{year}/Schedule")
            return papers
        
        base_url = f"https://proceedings.mlr.press/v{volume}/"
        
        response = requests.get(base_url, timeout=30)
        response.raise_for_status()
        
        # 解析HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 查找论文条目
        # PMLR格式：每篇论文在 <div class="paper"> 中
        paper_divs = soup.find_all('div', class_='paper')
        
        if not paper_divs:
            # 尝试其他选择器
            paper_divs = soup.find_all('p', class_='title')
        
        for paper_div in paper_divs:
            try:
                # 查找标题
                title_elem = paper_div.find('span', class_='title') or paper_div.find('a')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    
                    # 查找链接
                    link_elem = paper_div.find('a', href=True)
                    url = ''
                    if link_elem:
                        href = link_elem['href']
                        if href.startswith('http'):
                            url = href
                        else:
                            url = f"https://proceedings.mlr.press{href}"
                    
                    if title and len(title) > 10:
                        papers.append({
                            'title': title,
                            'url': url,
                            'source': f'ICML{year}'
                        })
                        
            except Exception as e:
                logger.warning(f"Error parsing paper entry: {e}")
                continue
        
        logger.info(f"Successfully collected {len(papers)} papers from ICML {year}")
        return papers
        
    except Exception as e:
        logger.error(f"Error collecting ICML papers: {e}")
        return papers

