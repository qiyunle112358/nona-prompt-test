"""
快速验证脚本
检查数据库、PDF和文本文件的状态
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Database
from config import DB_PATH, PDF_DIR, TEXT_DIR

def main():
    print("="*80)
    print("快速验证")
    print("="*80)
    
    # 检查数据库
    if DB_PATH.exists():
        db = Database(str(DB_PATH))
        stats = db.get_statistics()
        
        print(f"\n📊 数据库状态:")
        print(f"  总论文数: {stats['total_papers']}")
        print(f"  状态分布: {stats['status_counts']}")
        print(f"  已分析: {stats['analyzed_papers']}")
        print(f"  相关论文: {stats['relevant_papers']}")
        
        # 显示各状态的论文数量
        for status in ['pendingTitles', 'TobeDownloaded', 'processed', 'analyzed', 'detailFailed', 'downloadFailed']:
            papers = db.get_papers_by_status(status)
            if papers:
                print(f"\n  {status.upper()} ({len(papers)} 篇):")
                for paper in papers[:3]:
                    print(f"    - {paper['title'][:60]}...")

        failure_counts = stats.get('failure_counts', {})
        if failure_counts:
            print("\n⚠️ 失败记录:")
            print(f"  详情获取失败: {failure_counts.get('detail_failures', 0)} 条")
            print(f"  PDF下载失败: {failure_counts.get('download_failures', 0)} 条")
    else:
        print("\n📊 数据库: 不存在")
    
    # 检查PDF文件
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    print(f"\n📄 PDF文件: {len(pdf_files)} 个")
    if pdf_files:
        total_size = sum(f.stat().st_size for f in pdf_files) / (1024 * 1024)
        print(f"  总大小: {total_size:.2f}MB")
        for pdf in pdf_files[:5]:
            size = pdf.stat().st_size / (1024 * 1024)
            print(f"    {pdf.name}: {size:.2f}MB")
        if len(pdf_files) > 5:
            print(f"    ... 还有 {len(pdf_files) - 5} 个文件")
    else:
        print("  (无PDF文件)")
    
    # 检查文本文件
    text_files = list(TEXT_DIR.glob("*.txt"))
    print(f"\n📝 文本文件: {len(text_files)} 个")
    if text_files:
        total_size = sum(f.stat().st_size for f in text_files) / 1024
        print(f"  总大小: {total_size:.2f}KB")
        for txt in text_files[:5]:
            size = txt.stat().st_size / 1024
            print(f"    {txt.name}: {size:.1f}KB")
        if len(text_files) > 5:
            print(f"    ... 还有 {len(text_files) - 5} 个文件")
    else:
        print("  (无文本文件)")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()

