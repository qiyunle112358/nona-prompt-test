"""
清理和整理data文件夹
"""

import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_prompt_test():
    """清理prompt_test目录中的临时文件和重复文件"""
    base_dir = Path("data/prompt_test")
    
    if not base_dir.exists():
        logger.info("prompt_test目录不存在，无需清理")
        return
    
    logger.info("开始清理prompt_test目录...")
    
    # 1. 删除.DS_Store文件
    for ds_file in base_dir.rglob(".DS_Store"):
        ds_file.unlink()
        logger.info(f"删除: {ds_file}")
    
    # 2. 删除临时文件
    for temp_file in base_dir.rglob("temp_*"):
        temp_file.unlink()
        logger.info(f"删除临时文件: {temp_file}")
    
    # 3. 整理：保留results目录，清理其他临时目录
    # original_images和generated_images中的文件已经在results中，可以删除
    original_dir = base_dir / "original_images"
    generated_dir = base_dir / "generated_images"
    images_dir = base_dir / "images"
    
    if original_dir.exists():
        logger.info(f"清理original_images目录（{sum(1 for _ in original_dir.rglob('*'))} 个文件）...")
        shutil.rmtree(original_dir)
        logger.info("✓ 已删除original_images目录")
    
    if generated_dir.exists():
        logger.info(f"清理generated_images目录（{sum(1 for _ in generated_dir.rglob('*'))} 个文件）...")
        shutil.rmtree(generated_dir)
        logger.info("✓ 已删除generated_images目录")
    
    if images_dir.exists():
        logger.info(f"清理images目录（{sum(1 for _ in images_dir.rglob('*'))} 个文件）...")
        shutil.rmtree(images_dir)
        logger.info("✓ 已删除images目录")
    
    logger.info("✓ prompt_test目录清理完成")
    logger.info(f"保留的results目录: {base_dir / 'results'}")
    logger.info(f"  包含 {len(list((base_dir / 'results').rglob('*.png')))} 张图片")


def organize_data_folder():
    """整理整个data文件夹"""
    data_dir = Path("data")
    
    if not data_dir.exists():
        logger.info("data目录不存在")
        return
    
    logger.info("="*60)
    logger.info("整理data文件夹")
    logger.info("="*60)
    
    # 显示当前结构
    logger.info("\n当前data目录结构:")
    for item in sorted(data_dir.iterdir()):
        if item.is_dir():
            size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
            logger.info(f"  {item.name}/ ({size / 1024 / 1024:.1f} MB)")
        else:
            size = item.stat().st_size
            logger.info(f"  {item.name} ({size / 1024:.1f} KB)")
    
    # 清理prompt_test
    cleanup_prompt_test()
    
    logger.info("\n" + "="*60)
    logger.info("整理完成！")
    logger.info("="*60)
    
    # 显示整理后的结构
    logger.info("\n整理后的data目录结构:")
    for item in sorted(data_dir.iterdir()):
        if item.is_dir():
            size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
            file_count = len(list(item.rglob('*')))
            logger.info(f"  {item.name}/ ({size / 1024 / 1024:.1f} MB, {file_count} 个文件)")
        else:
            size = item.stat().st_size
            logger.info(f"  {item.name} ({size / 1024:.1f} KB)")


if __name__ == '__main__':
    organize_data_folder()
