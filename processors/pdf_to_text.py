"""
PDF转文本处理器
优先使用 pdfplumber 提取文本，失败时回退到 PyPDF2
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict

import pdfplumber
import PyPDF2
from tqdm import tqdm

logger = logging.getLogger(__name__)
_feature_warned: set = set()


def convert_pdf_to_text(
    pdf_path: Path,
    text_path: Path,
    extract_tables: bool = True,
    extract_formulas: bool = True,
) -> bool:
    """
    使用 pdfplumber 将PDF转换为文本，失败时回退 PyPDF2
    """
    if text_path.exists():
        logger.info("Text already exists: %s", text_path.name)
        return True

    try:
        logger.info("Converting PDF to text: %s", pdf_path.name)
        raw_text = _extract_text(pdf_path)
        if not raw_text.strip():
            logger.warning("Primary extractor returned empty text for %s", pdf_path)
            return False

        cleaned_text = _clean_text(raw_text)
        _maybe_warn_feature("tables", extract_tables)
        _maybe_warn_feature("formulas", extract_formulas)

        text_path.parent.mkdir(parents=True, exist_ok=True)
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)

        logger.info("✓ Converted: %s (%.1fKB)", text_path.name, text_path.stat().st_size / 1024)
        return True
    except Exception as exc:
        logger.error("Error converting PDF to text: %s", exc)
        if text_path.exists():
            text_path.unlink()
        return False


def batch_convert_pdfs(
    papers: List[Dict],
    pdf_dir: Path,
    text_dir: Path,
    extract_tables: bool = True,
    extract_formulas: bool = True,
    show_progress: bool = True,
) -> int:
    success_count = 0
    iterator = tqdm(papers, desc="Converting PDFs") if show_progress else papers

    for paper in iterator:
        paper_id = paper.get("arxiv_id") or paper.get("id")
        if not paper_id:
            logger.warning("Missing paper ID for: %s", paper.get("title"))
            continue

        pdf_path = pdf_dir / f"{paper_id}.pdf"
        text_path = text_dir / f"{paper_id}.txt"

        if not pdf_path.exists():
            logger.warning("PDF not found: %s", pdf_path)
            continue

        try:
            if convert_pdf_to_text(pdf_path, text_path, extract_tables, extract_formulas):
                success_count += 1
        except Exception as exc:
            logger.error("Error processing paper %s: %s", paper_id, exc)
            continue

    logger.info("Successfully converted %d/%d PDFs", success_count, len(papers))
    return success_count


def _extract_text(pdf_path: Path) -> str:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            parts = []
            for page in pdf.pages:
                try:
                    parts.append(page.extract_text() or "")
                except Exception as exc:
                    logger.debug("pdfplumber failed on page %s: %s", page.page_number, exc)
                    continue
            return "\n".join(parts)
    except Exception as exc:
        logger.warning("pdfplumber failed on %s (%s), falling back to PyPDF2...", pdf_path.name, exc)
        return _extract_text_pypdf2(pdf_path)


def _extract_text_pypdf2(pdf_path: Path) -> str:
    try:
        reader = PyPDF2.PdfReader(str(pdf_path))
    except Exception as exc:
        logger.error("PyPDF2 failed to open %s: %s", pdf_path, exc)
        return ""

    texts = []
    for idx, page in enumerate(reader.pages):
        try:
            texts.append(page.extract_text() or "")
        except Exception as exc:
            logger.warning("PyPDF2 failed on page %s: %s", idx + 1, exc)
            continue
    return "\n".join(texts)


def _clean_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def _maybe_warn_feature(feature: str, enabled: bool) -> None:
    if enabled and feature not in _feature_warned:
        logger.info("Feature '%s' is not implemented in pdfminer workflow yet.", feature)
        _feature_warned.add(feature)


def get_text_path(paper_id: str, text_dir: Path) -> Optional[Path]:
    text_path = text_dir / f"{paper_id}.txt"
    return text_path if text_path.exists() else None


