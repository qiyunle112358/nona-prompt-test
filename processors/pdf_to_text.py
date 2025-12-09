import logging
from pathlib import Path
from typing import Optional, List, Dict
import fitz  # PyMuPDF
import re
from tqdm import tqdm

logger = logging.getLogger(__name__)


def convert_pdf_to_text(
    pdf_path: Path,
    text_path: Path,
    extract_tables: bool = True,
    extract_formulas: bool = True
) -> bool:
    """
    将PDF转换为文本

    Args:
        pdf_path: PDF文件路径
        text_path: 文本保存路径
        extract_tables: 是否提取表格
        extract_formulas: 是否提取公式

    Returns:
        是否转换成功
    """
    # 如果文本已存在，跳过转换
    if text_path.exists():
        logger.info(f"Text already exists: {text_path.name}")
        return True

    try:
        logger.info(f"Converting PDF to text: {pdf_path.name}")

        # 打开PDF
        doc = fitz.open(pdf_path)

        # 提取文本内容
        full_text = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # 添加页码标记
            full_text.append(f"\n{'='*80}\n")
            full_text.append(f"Page {page_num + 1}\n")
            full_text.append(f"{'='*80}\n\n")

            # 提取文本
            text = page.get_text("text")

            # 清理文本
            text = _clean_text(text)

            full_text.append(text)

            # 提取表格（转为Markdown格式）
            if extract_tables:
                tables = _extract_tables_from_page(page)
                if tables:
                    full_text.append("\n\n### Tables ###\n")
                    for i, table in enumerate(tables, 1):
                        full_text.append(f"\n#### Table {i} ####\n")
                        full_text.append(table)
                        full_text.append("\n")

            # 提取公式（尝试保留LaTeX格式）
            if extract_formulas:
                formulas = _extract_formulas_from_page(page)
                if formulas:
                    full_text.append("\n\n### Formulas ###\n")
                    for formula in formulas:
                        full_text.append(f"{formula}\n")

        doc.close()

        # 保存文本
        text_path.parent.mkdir(parents=True, exist_ok=True)

        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(''.join(full_text))

        text_size = text_path.stat().st_size
        logger.info(f"✓ Converted: {text_path.name} ({text_size / 1024:.1f}KB)")
        return True

    except Exception as e:
        logger.error(f"Error converting PDF to text: {e}")
        # 删除可能部分写入的文件
        if text_path.exists():
            text_path.unlink()
        return False


def batch_convert_pdfs(
    papers: List[Dict],
    pdf_dir: Path,
    text_dir: Path,
    extract_tables: bool = True,
    extract_formulas: bool = True,
    show_progress: bool = True
) -> int:
    """
    批量转换PDF为文本

    Args:
        papers: 论文列表
        pdf_dir: PDF目录
        text_dir: 文本保存目录
        extract_tables: 是否提取表格
        extract_formulas: 是否提取公式
        show_progress: 是否显示进度条

    Returns:
        成功转换的数量
    """
    success_count = 0

    iterator = tqdm(papers, desc="Converting PDFs") if show_progress else papers

    for paper in iterator:
        paper_id = paper.get('arxiv_id') or paper.get('id')

        if not paper_id:
            logger.warning(f"Missing paper ID for: {paper.get('title')}")
            continue

        pdf_path = pdf_dir / f"{paper_id}.pdf"
        text_path = text_dir / f"{paper_id}.txt"

        if not pdf_path.exists():
            logger.warning(f"PDF not found: {pdf_path}")
            continue

        try:
            if convert_pdf_to_text(pdf_path, text_path, extract_tables, extract_formulas):
                success_count += 1

        except Exception as e:
            logger.error(f"Error processing paper {paper_id}: {e}")
            continue

    logger.info(f"Successfully converted {success_count}/{len(papers)} PDFs")
    return success_count


def _clean_text(text: str) -> str:
    """
    清理提取的文本
    - 移除多余的空白行
    - 修复断行
    """
    # 移除多余的空白
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        line = line.strip()
        if line:
            cleaned_lines.append(line)

    # 合并被断开的行（简单启发式）
    result = []
    i = 0
    while i < len(cleaned_lines):
        line = cleaned_lines[i]

        # 如果行以连字符结尾，可能是断行
        if i < len(cleaned_lines) - 1 and line.endswith('-'):
            # 移除连字符并合并
            line = line[:-1] + cleaned_lines[i + 1]
            i += 2
        else:
            # 如果行不以句号等结尾，且下一行以小写开头，可能是断行
            if (i < len(cleaned_lines) - 1 and
                not line[-1] in '.!?:;' and
                cleaned_lines[i + 1] and
                cleaned_lines[i + 1][0].islower()):
                line = line + ' ' + cleaned_lines[i + 1]
                i += 2
            else:
                i += 1

        result.append(line)

    return '\n'.join(result)


def _extract_tables_from_page(page) -> List[str]:
    """
    从页面提取表格（转为Markdown格式）
    这是一个简化版本，实际应用中可以使用camelot或tabula
    """
    tables = []

    try:
        # PyMuPDF的表格提取功能有限
        # 这里提供一个占位符，实际使用时建议使用camelot-py或tabula-py

        # 获取页面中的表格区域（基于文本块的位置）
        blocks = page.get_text("blocks")

        # 简单的表格检测：查找对齐的文本块
        # 这是一个非常简化的实现

        # TODO: 集成camelot-py或tabula-py进行更准确的表格提取

        pass

    except Exception as e:
        logger.debug(f"Error extracting tables: {e}")

    return tables


def _extract_formulas_from_page(page) -> List[str]:
    """
    从页面提取数学公式
    尝试保留LaTeX格式
    """
    formulas = []

    try:
        # PyMuPDF可以提取一些LaTeX内容
        text = page.get_text("text")

        # 查找可能的公式模式（简单启发式）
        # 查找包含数学符号的行
        math_symbols = r'[∑∫∂∇⊗⊕±≤≥≠≈∞√∏α-ωΑ-Ω]'

        lines = text.split('\n')
        for line in lines:
            if re.search(math_symbols, line):
                formulas.append(line.strip())

        # TODO: 更复杂的公式识别可以使用Mathpix或其他OCR服务

    except Exception as e:
        logger.debug(f"Error extracting formulas: {e}")

    return formulas


def get_text_path(paper_id: str, text_dir: Path) -> Optional[Path]:
    """
    获取文本文件路径

    Args:
        paper_id: 论文ID
        text_dir: 文本目录

    Returns:
        文本路径，如果不存在返回None
    """
    text_path = text_dir / f"{paper_id}.txt"
    return text_path if text_path.exists() else None
