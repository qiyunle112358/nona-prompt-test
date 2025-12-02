"""
PDF处理和OCR模块
下载PDF并转换为结构化文本
"""

from .pdf_downloader import download_pdf, batch_download_pdfs
from .pdf_to_text import convert_pdf_to_text, batch_convert_pdfs

__all__ = [
    'download_pdf',
    'batch_download_pdfs',
    'convert_pdf_to_text',
    'batch_convert_pdfs'
]

