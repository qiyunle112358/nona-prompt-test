"""
PDF下载器
从URL下载PDF文件到本地
"""

import logging
import requests
from pathlib import Path
from typing import Optional, List, Dict
from tqdm import tqdm
import time

logger = logging.getLogger(__name__)


def download_pdf(pdf_url: str, save_path: Path, max_size_mb: int = 50) -> bool:
    """
    下载PDF文件
    
    Args:
        pdf_url: PDF文件URL
        save_path: 保存路径
        max_size_mb: 最大文件大小（MB）
        
    Returns:
        是否下载成功
    """
    # 如果文件已存在，跳过下载
    if save_path.exists():
        logger.info(f"PDF already exists: {save_path.name}")
        return True
    
    try:
        logger.info(f"Downloading PDF from: {pdf_url}")
        
        # 直接下载整个文件（不使用stream模式，避免卡住）
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        # 检查文件大小
        file_size = len(response.content)
        max_size = max_size_mb * 1024 * 1024
        
        if file_size > max_size:
            logger.warning(f"PDF too large: {file_size / 1024 / 1024:.1f}MB (max: {max_size_mb}MB)")
            return False
        
        # 检查Content-Type
        content_type = response.headers.get('Content-Type', '')
        if 'application/pdf' not in content_type and 'octet-stream' not in content_type:
            logger.warning(f"URL did not return a PDF. Content-Type: {content_type}")
            return False
        
        # 保存文件
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"✓ Downloaded: {save_path.name} ({file_size / 1024 / 1024:.1f}MB)")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading PDF from {pdf_url}: {e}")
        # 删除可能部分下载的文件
        if save_path.exists():
            save_path.unlink()
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading PDF: {e}")
        if save_path.exists():
            save_path.unlink()
        return False


def batch_download_pdfs(
    papers: List[Dict],
    pdf_dir: Path,
    max_size_mb: int = 50,
    show_progress: bool = True
) -> int:
    """
    批量下载PDF文件
    
    Args:
        papers: 论文列表，每个元素应包含'arxiv_id'和'pdf_url'
        pdf_dir: PDF保存目录
        max_size_mb: 最大文件大小（MB）
        show_progress: 是否显示进度条
        
    Returns:
        成功下载的数量
    """
    success_count = 0
    
    iterator = tqdm(papers, desc="Downloading PDFs") if show_progress else papers
    
    for paper in iterator:
        arxiv_id = paper.get('arxiv_id') or paper.get('id')
        pdf_url = paper.get('pdf_url')
        
        if not arxiv_id or not pdf_url:
            logger.warning(f"Missing arxiv_id or pdf_url for paper: {paper.get('title')}")
            continue
        
        # 构建保存路径
        save_path = pdf_dir / f"{arxiv_id}.pdf"
        
        try:
            if download_pdf(pdf_url, save_path, max_size_mb):
                success_count += 1
            
            # 避免请求过快
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error processing paper {arxiv_id}: {e}")
            continue
    
    logger.info(f"Successfully downloaded {success_count}/{len(papers)} PDFs")
    return success_count


def get_pdf_path(paper_id: str, pdf_dir: Path) -> Optional[Path]:
    """
    获取PDF文件路径
    
    Args:
        paper_id: 论文ID（通常是arxiv_id）
        pdf_dir: PDF目录
        
    Returns:
        PDF路径，如果不存在返回None
    """
    pdf_path = pdf_dir / f"{paper_id}.pdf"
    return pdf_path if pdf_path.exists() else None

