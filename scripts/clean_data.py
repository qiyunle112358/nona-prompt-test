"""
清理数据脚本
删除数据库、PDF和文本文件
"""

import sys
from pathlib import Path
import shutil

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_PATH, PDF_DIR, TEXT_DIR, DATA_DIR

def clean_all():
    """清理所有数据"""
    print("="*80)
    print("清理数据")
    print("="*80)
    
    # 删除数据库
    if DB_PATH.exists():
        print(f"删除数据库: {DB_PATH}")
        DB_PATH.unlink()
        print("✓ 数据库已删除")
    else:
        print("数据库不存在，跳过")
    
    # 删除PDF文件
    if PDF_DIR.exists():
        pdf_files = list(PDF_DIR.glob("*.pdf"))
        if pdf_files:
            print(f"\n删除PDF文件: {len(pdf_files)} 个")
            for pdf_file in pdf_files:
                pdf_file.unlink()
            print("✓ PDF文件已删除")
        else:
            print("\nPDF目录为空，跳过")
    else:
        print("\nPDF目录不存在，跳过")
    
    # 删除文本文件
    if TEXT_DIR.exists():
        text_files = list(TEXT_DIR.glob("*.txt"))
        if text_files:
            print(f"\n删除文本文件: {len(text_files)} 个")
            for text_file in text_files:
                text_file.unlink()
            print("✓ 文本文件已删除")
        else:
            print("\n文本目录为空，跳过")
    else:
        print("\n文本目录不存在，跳过")
    
    print("\n" + "="*80)
    print("✓ 数据清理完成")
    print("="*80)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='清理数据')
    parser.add_argument('--confirm', action='store_true', help='确认删除（必须提供此参数）')
    
    args = parser.parse_args()
    
    if not args.confirm:
        print("警告：此操作将删除所有数据！")
        print("如果确定要删除，请使用: python scripts/clean_data.py --confirm")
        sys.exit(1)
    
    clean_all()

