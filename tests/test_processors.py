"""
PDF处理器测试
下载1个样本PDF并转换为文本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


# 测试用的样本PDF（小文件，快速下载）
TEST_PDF = {
    'arxiv_id': '1706.03762',  # Attention Is All You Need
    'pdf_url': 'https://arxiv.org/pdf/1706.03762.pdf',
    'title': 'Attention Is All You Need'
}


def test_processors():
    """测试PDF处理器"""
    logger.info("="*60)
    logger.info("测试：PDF处理器")
    logger.info("="*60)
    logger.info(f"测试论文: {TEST_PDF['title']}")
    logger.info("="*60)
    
    # 使用临时目录
    temp_dir = Path(__file__).parent / "temp"
    temp_pdf_dir = temp_dir / "pdfs"
    temp_text_dir = temp_dir / "texts"
    
    temp_pdf_dir.mkdir(parents=True, exist_ok=True)
    temp_text_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        from processors import download_pdf, convert_pdf_to_text
        
        # 测试1: 下载PDF
        logger.info("\n[测试1] 下载PDF")
        logger.info(f"下载到: {temp_pdf_dir}")
        
        pdf_path = temp_pdf_dir / f"{TEST_PDF['arxiv_id']}.pdf"
        
        result = download_pdf(
            pdf_url=TEST_PDF['pdf_url'],
            save_path=pdf_path,
            max_size_mb=50
        )
        
        assert result, "PDF下载失败"
        assert pdf_path.exists(), "PDF文件不存在"
        
        file_size = pdf_path.stat().st_size / (1024 * 1024)
        logger.info(f"✓ PDF下载成功")
        logger.info(f"  文件大小: {file_size:.2f} MB")
        logger.info(f"  保存路径: {pdf_path}")
        
        # 测试2: 转换为文本
        logger.info("\n[测试2] 转换为文本")
        
        text_path = temp_text_dir / f"{TEST_PDF['arxiv_id']}.txt"
        
        result = convert_pdf_to_text(
            pdf_path=pdf_path,
            text_path=text_path,
            extract_tables=True,
            extract_formulas=True
        )
        
        assert result, "文本转换失败"
        assert text_path.exists(), "文本文件不存在"
        
        # 读取并验证文本
        with open(text_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        text_size = len(text_content)
        logger.info(f"✓ 文本转换成功")
        logger.info(f"  文本长度: {text_size} 字符")
        logger.info(f"  保存路径: {text_path}")
        
        # 显示文本预览
        logger.info("\n文本预览（前500字符）:")
        logger.info("-"*60)
        logger.info(text_content[:500])
        logger.info("...")
        logger.info("-"*60)
        
        # 测试3: 重复处理（幂等性）
        logger.info("\n[测试3] 幂等性测试")
        logger.info("再次下载和转换（应该跳过）...")
        
        result1 = download_pdf(TEST_PDF['pdf_url'], pdf_path)
        result2 = convert_pdf_to_text(pdf_path, text_path)
        
        assert result1 and result2, "幂等性测试失败"
        logger.info("✓ 幂等性测试通过（正确跳过已存在的文件）")
        
        logger.info("\n" + "="*60)
        logger.info("✓ PDF处理器测试通过")
        logger.info("="*60)
        logger.info(f"\n测试文件保存在: {temp_dir}")
        logger.info("可以手动检查PDF和文本文件的质量")
        
        return True
        
    except Exception as e:
        logger.error(f"\n✗ PDF处理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_processors()
    sys.exit(0 if success else 1)

