"""
运行所有测试
"""

import sys
from pathlib import Path
import subprocess
import time

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def run_test(test_file: str, description: str) -> bool:
    """运行单个测试"""
    logger.info("\n" + "="*80)
    logger.info(f"运行测试: {description}")
    logger.info("="*80)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            cwd=project_root,
            capture_output=False,
            text=True
        )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            logger.info(f"\n✓ {description} 通过 (耗时: {elapsed:.1f}秒)")
            return True
        else:
            logger.error(f"\n✗ {description} 失败 (耗时: {elapsed:.1f}秒)")
            return False
            
    except Exception as e:
        logger.error(f"\n✗ {description} 执行出错: {e}")
        return False


def main():
    """运行所有测试"""
    import argparse
    
    parser = argparse.ArgumentParser(description='运行所有测试')
    parser.add_argument('--skip-api', action='store_true', help='跳过需要API的测试')
    parser.add_argument('--skip-network', action='store_true', help='跳过需要网络的测试')
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("具身智能论文Survey工具 - 测试套件")
    logger.info("="*80)
    
    tests_dir = Path(__file__).parent
    
    # 定义测试列表
    tests = [
        {
            'file': tests_dir / 'test_config.py',
            'description': '配置模块测试',
            'requires_network': False,
            'requires_api': False
        },
        {
            'file': tests_dir / 'test_database.py',
            'description': '数据库模块测试',
            'requires_network': False,
            'requires_api': False
        },
        {
            'file': tests_dir / 'test_collectors.py',
            'description': '论文收集器测试',
            'requires_network': True,
            'requires_api': False
        },
        {
            'file': tests_dir / 'test_fetchers.py',
            'description': '论文信息获取器测试',
            'requires_network': True,
            'requires_api': False
        },
        {
            'file': tests_dir / 'test_processors.py',
            'description': 'PDF处理器测试',
            'requires_network': True,
            'requires_api': False
        },
        {
            'file': tests_dir / 'test_analyzers.py',
            'description': 'AI分析器测试',
            'requires_network': True,
            'requires_api': True
        },
    ]
    
    # 运行测试
    results = []
    
    for test in tests:
        # 检查是否跳过
        if args.skip_network and test['requires_network']:
            logger.info(f"\n⊘ 跳过: {test['description']} (需要网络)")
            continue
        
        if args.skip_api and test['requires_api']:
            logger.info(f"\n⊘ 跳过: {test['description']} (需要API)")
            continue
        
        # 运行测试
        success = run_test(str(test['file']), test['description'])
        results.append({
            'description': test['description'],
            'success': success
        })
    
    # 显示总结
    logger.info("\n\n" + "="*80)
    logger.info("测试总结")
    logger.info("="*80)
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    for result in results:
        status = "✓ 通过" if result['success'] else "✗ 失败"
        logger.info(f"{status} - {result['description']}")
    
    logger.info("="*80)
    logger.info(f"总计: {passed}/{total} 通过")
    
    if passed == total:
        logger.info("✓ 所有测试通过！")
        logger.info("="*80)
        return 0
    else:
        logger.error(f"✗ {total - passed} 个测试失败")
        logger.info("="*80)
        return 1


if __name__ == "__main__":
    sys.exit(main())

