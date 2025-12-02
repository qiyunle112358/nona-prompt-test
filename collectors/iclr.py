"""
ICLR论文收集器
从ICLR会议网站收集论文标题
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import json

logger = logging.getLogger(__name__)


def collect_iclr_papers(year: int = 2025) -> List[Dict[str, str]]:
    """
    收集ICLR论文标题
    
    Args:
        year: 会议年份
        
    Returns:
        论文列表，每个元素包含 {title, url, source}
    """
    logger.info(f"Collecting ICLR {year} papers")
    
    papers = []
    
    try:
        # ICLR使用OpenReview平台
        # API endpoint
        base_url = f"https://api.openreview.net/notes"
        
        # 构建查询参数
        params = {
            'invitation': f'ICLR.cc/{year}/Conference/-/Blind_Submission',
            'details': 'replyCount,invitation',
            'limit': 1000,
            'offset': 0
        }
        
        while True:
            try:
                response = requests.get(base_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                notes = data.get('notes', [])
                
                if not notes:
                    break
                
                for note in notes:
                    try:
                        content = note.get('content', {})
                        title = content.get('title', '')
                        
                        if title:
                            papers.append({
                                'title': title.strip(),
                                'url': f"https://openreview.net/forum?id={note.get('id', '')}",
                                'source': f'ICLR{year}'
                            })
                    except Exception as e:
                        logger.warning(f"Error parsing note: {e}")
                        continue
                
                # 检查是否还有更多结果
                if len(notes) < params['limit']:
                    break
                
                params['offset'] += params['limit']
                logger.info(f"Collected {len(papers)} papers so far...")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching from OpenReview API: {e}")
                break
        
        logger.info(f"Successfully collected {len(papers)} papers from ICLR {year}")
        return papers
        
    except Exception as e:
        logger.error(f"Error collecting ICLR papers: {e}")
        return papers

