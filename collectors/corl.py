"""
CoRL论文收集器
从CoRL (Conference on Robot Learning) 会议网站收集论文标题
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict

logger = logging.getLogger(__name__)


def collect_corl_papers(year: int = 2024) -> List[Dict[str, str]]:
    """
    收集CoRL论文标题
    
    Args:
        year: 会议年份
        
    Returns:
        论文列表，每个元素包含 {title, url, source}
    """
    logger.info(f"Collecting CoRL {year} papers")
    
    papers = []
    
    try:
        # CoRL使用PMLR
        # URL格式：https://proceedings.mlr.press/v{volume}/
        
        # CoRL卷号映射
        volume_mapping = {
            2024: 229,  # CoRL 2024 (需要确认)
            2023: 229,  # CoRL 2023
            2022: 205,  # CoRL 2022
        }
        
        volume = volume_mapping.get(year)
        if not volume:
            logger.warning(f"Unknown volume for CoRL {year}. Please update volume_mapping.")
            logger.info(f"Manual collection recommended: Visit https://www.corl.org/")
            return papers
        
        base_url = f"https://proceedings.mlr.press/v{volume}/"
        
        response = requests.get(base_url, timeout=30)
        response.raise_for_status()
        
        # 解析HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 查找论文条目
        paper_divs = soup.find_all('div', class_='paper')
        
        if not paper_divs:
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
                            'source': f'CoRL{year}'
                        })
                        
            except Exception as e:
                logger.warning(f"Error parsing paper entry: {e}")
                continue
        
        logger.info(f"Successfully collected {len(papers)} papers from CoRL {year}")
        return papers
        
    except Exception as e:
        logger.error(f"Error collecting CoRL papers: {e}")
        return papers

