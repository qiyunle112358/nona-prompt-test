"""
图片Prompt测试脚本 - 优化版本
优化点：
1. 并行处理多个论文
2. 异步并行生成图片
3. 并行评估相似度
4. 进度保存和断点续传
5. 智能重试机制
"""

import argparse
import logging
import sys
import random
import os
import base64
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import requests
from PIL import Image
import fitz  # PyMuPDF

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_PATH, PDF_DIR, LOG_LEVEL, LOG_FORMAT
from database import Database
import collectors
from scripts.image_similarity import ImageSimilarityEvaluator

# 配置日志
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# 不同领域的arXiv分类
ARXIV_CATEGORIES = [
    'cs.CV', 'cs.CL', 'cs.LG', 'cs.AI', 'cs.RO', 'cs.GR',
    'physics.optics', 'physics.med-ph', 'q-bio.BM', 'math.OC',
    'stat.ML', 'eess.IV',
]

# 前置prompt（用于生图）
IMAGE_GENERATION_PREFIX = """You are an expert scientific illustrator and data visualization specialist for high-impact academic journals... Your Goal: Translate technical concepts, data, requirements, or architectures provided by the user into high-quality, publication-ready visualization images... Interaction Protocol: When the user provides a request, strictly follow their specified object description and constraints to generate the corresponding visual representation... **IMPORTANT**: Generate at least one image."""

# 全局锁和进度跟踪
progress_lock = Lock()
processed_papers = set()
progress_file = None


class OpenRouterClient:
    """OpenRouter API客户端（支持重试）"""
    
    def __init__(self, api_key: str, max_retries: int = 3):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.max_retries = max_retries
    
    def _retry_request(self, func, *args, **kwargs):
        """重试机制"""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = 2 ** attempt  # 指数退避
                logger.warning(f"请求失败，{wait_time}秒后重试 (尝试 {attempt+1}/{self.max_retries}): {e}")
                time.sleep(wait_time)
        return None
    
    def image_to_text(self, image_path: Path, num_prompts: int = 5) -> List[str]:
        """图生文：分析图片并生成prompt"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            ext = image_path.suffix.lower()
            mime_types = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}
            mime_type = mime_types.get(ext, 'image/png')
            image_url = f"data:{mime_type};base64,{image_base64}"
            
            prompt_text = f"""Analyze this scientific/academic diagram/flowchart image and generate exactly {num_prompts} different extremely detailed prompts that could be used to recreate an image as identical as possible to the original.

CRITICAL REQUIREMENTS:
- Return ONLY the {num_prompts} prompts, nothing else
- Start directly with "1." followed by the first prompt
- Do NOT include any introductory text like "Here are...", "The following...", etc.
- Each prompt should be on a separate line, numbered as "1.", "2.", "3.", etc.
- Use a blank line between each prompt for clarity

Each prompt MUST be extremely detailed and describe EVERY aspect of the image:
1. **Layout and Structure**: Exact positioning, arrangement, alignment of all elements
2. **Visual Elements**: Every shape, box, circle, arrow, line, connector - their exact positions, sizes, orientations
3. **Text and Labels**: All text content, labels, annotations, their exact positions and fonts
4. **Colors**: Exact color scheme for each element (use specific color names or hex codes)
5. **Connections**: All arrows, lines, connections between elements - their directions, styles, endpoints
6. **Styling**: Line thickness, border styles, fill patterns, shadows, gradients
7. **Spacing**: Exact distances, margins, padding between elements
8. **Background**: Background color, patterns, or transparency
9. **Typography**: Font sizes, weights, styles for all text elements
10. **Overall Style**: Scientific diagram style, academic paper style, etc.

The goal is to create prompts so detailed that the generated image will be as identical as possible to the original image. Describe every single detail you can observe.

Format:
1. [First extremely detailed prompt]
2. [Second extremely detailed prompt]
3. [Third extremely detailed prompt]
4. [Fourth extremely detailed prompt]
5. [Fifth extremely detailed prompt]"""

            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": "google/gemini-2.5-flash",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": prompt_text}
                    ]
                }]
            }
            
            def make_request():
                response = requests.post(url, headers=self.headers, json=payload, timeout=60)
                if response.status_code != 200:
                    raise Exception(f"API请求失败: {response.status_code} - {response.text}")
                return response.json()
            
            result = self._retry_request(make_request)
            if not result:
                return []
            
            # 解析prompt（简化版，使用原有逻辑）
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                # 这里应该使用原有的prompt解析逻辑
                prompts = self._parse_prompts(content, num_prompts)
                return prompts
            return []
        except Exception as e:
            logger.error(f"分析图片时出错 {image_path}: {e}")
            return []
    
    def _parse_prompts(self, content: str, num_prompts: int) -> List[str]:
        """解析prompt（简化版）"""
        # 这里应该使用原有的完整解析逻辑
        prompts = []
        lines = content.split('\n')
        current_prompt = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_prompt:
                    prompts.append(' '.join(current_prompt))
                    current_prompt = []
                continue
            
            # 检查是否是新的prompt开始
            if line[0].isdigit() and ('.' in line[:3] or ':' in line[:3]):
                if current_prompt:
                    prompts.append(' '.join(current_prompt))
                current_prompt = [line.split('.', 1)[-1].strip() if '.' in line else line.split(':', 1)[-1].strip()]
            else:
                current_prompt.append(line)
        
        if current_prompt:
            prompts.append(' '.join(current_prompt))
        
        return prompts[:num_prompts] if len(prompts) >= num_prompts else prompts
    
    def text_to_image(self, prompt: str, output_path: Path) -> bool:
        """文生图：根据prompt生成图片"""
        try:
            full_prompt = f"{IMAGE_GENERATION_PREFIX}\n\n{prompt}"
            
            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": "google/gemini-3-pro-image-preview",
                "messages": [{
                    "role": "user",
                    "content": [{"type": "text", "text": full_prompt}]
                }],
                "modalities": ["image", "text"]
            }
            
            def make_request():
                response = requests.post(url, headers=self.headers, json=payload, timeout=300)
                if response.status_code != 200:
                    raise Exception(f"API请求失败: {response.status_code} - {response.text}")
                return response.json()
            
            result = self._retry_request(make_request)
            if not result:
                return False
            
            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0]["message"]
                if message.get("images"):
                    image_url = message["images"][0]["image_url"]["url"]
                    if image_url.startswith("data:image"):
                        image_data = base64.b64decode(image_url.split(",")[1])
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, 'wb') as f:
                            f.write(image_data)
                        return True
            return False
        except Exception as e:
            logger.error(f"生成图片时出错: {e}")
            return False


def save_progress(arxiv_id: str, output_dir: Path):
    """保存进度"""
    global processed_papers, progress_file
    with progress_lock:
        processed_papers.add(arxiv_id)
        if progress_file:
            with open(progress_file, 'a') as f:
                f.write(f"{arxiv_id}\n")


def load_progress(output_dir: Path) -> set:
    """加载进度"""
    progress_file = output_dir / ".progress"
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def process_single_paper(paper: Dict, args, db: Database, api_client: OpenRouterClient, 
                        output_dir: Path, evaluator: ImageSimilarityEvaluator) -> Optional[Dict]:
    """处理单篇论文（可并行执行）"""
    arxiv_id = paper.get('arxiv_id')
    pdf_url = paper.get('pdf_url')
    
    if not arxiv_id or not pdf_url:
        return None
    
    # 检查是否已处理
    if arxiv_id in processed_papers:
        logger.info(f"跳过已处理的论文: {arxiv_id}")
        return None
    
    try:
        logger.info(f"处理论文: {paper['title'][:60]}... (ID: {arxiv_id})")
        
        # 下载PDF
        pdf_path = PDF_DIR / f"{arxiv_id}.pdf"
        if not pdf_path.exists():
            from processors import download_pdf
            if not download_pdf(pdf_url, pdf_path):
                logger.warning(f"PDF下载失败: {arxiv_id}")
                return None
        
        # 提取流程图
        from scripts.image_prompt_test import FlowchartExtractor
        extractor = FlowchartExtractor(pdf_path, output_dir / "original_images" / arxiv_id)
        flowchart_path = extractor.extract_flowchart()
        
        if not flowchart_path:
            logger.warning(f"未找到流程图: {arxiv_id}")
            db.delete_paper(paper['id'])
            return None
        
        # 生成prompt
        prompts = api_client.image_to_text(flowchart_path, args.num_prompts)
        if not prompts:
            logger.warning(f"未能生成prompt: {arxiv_id}")
            return None
        
        # 并行生成图片
        logger.info(f"并行生成 {len(prompts)} 张图片...")
        gen_dir = output_dir / "generated_images" / arxiv_id
        gen_dir.mkdir(parents=True, exist_ok=True)
        
        def generate_image(i, prompt):
            gen_path = gen_dir / f"prompt_{i}.png"
            if api_client.text_to_image(prompt, gen_path):
                return (i, gen_path, prompt)
            return None
        
        # 使用线程池并行生成
        generated_results = []
        with ThreadPoolExecutor(max_workers=3) as executor:  # 限制并发数避免API限流
            futures = {executor.submit(generate_image, i+1, p): i for i, p in enumerate(prompts)}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    generated_results.append(result)
                    logger.info(f"  ✓ Prompt {result[0]} 图片已生成")
        
        if not generated_results:
            logger.warning(f"所有图片生成失败: {arxiv_id}")
            return None
        
        # 按原始顺序排序
        generated_results.sort(key=lambda x: x[0])
        generated_paths = [r[1] for r in generated_results]
        generated_prompts = [r[2] for r in generated_results]
        
        # 并行评估相似度
        logger.info(f"并行评估 {len(generated_paths)} 张图片的相似度...")
        
        def evaluate_image(i, gen_path):
            scores = evaluator.evaluate_similarity(flowchart_path, gen_path)
            return {
                'index': i + 1,
                'path': gen_path,
                'prompt': generated_prompts[i],
                'scores': scores,
                'weighted_score': scores['weighted_score']
            }
        
        similarity_scores = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(evaluate_image, i, path): i for i, path in enumerate(generated_paths)}
            for future in as_completed(futures):
                result = future.result()
                similarity_scores.append(result)
                logger.info(f"  Prompt {result['index']} 相似度: {result['weighted_score']:.3f}")
        
        # 按加权得分排序
        similarity_scores.sort(key=lambda x: x['weighted_score'], reverse=True)
        
        # 保存结果
        result_dir = output_dir / "results" / arxiv_id
        result_dir.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy2(flowchart_path, result_dir / "original.png")
        
        for rank, item in enumerate(similarity_scores, 1):
            shutil.copy2(item['path'], result_dir / f"generated_{rank}.png")
        
        # 保存prompt文件
        prompts_file = result_dir / "prompts.txt"
        with open(prompts_file, 'w', encoding='utf-8') as f:
            f.write(f"论文: {paper['title']}\n")
            f.write(f"来源: {paper.get('source', 'N/A')}\n")
            f.write(f"arXiv ID: {arxiv_id}\n")
            f.write("="*80 + "\n\n")
            f.write("排名说明：按相似度得分从高到低排序\n")
            f.write("="*80 + "\n\n")
            
            for rank, item in enumerate(similarity_scores, 1):
                f.write(f"排名 {rank} (原始Prompt {item['index']}):\n")
                f.write(f"加权得分: {item['weighted_score']:.4f}\n")
                f.write(f"  - SSIM: {item['scores']['ssim']:.4f}\n")
                f.write(f"  - 特征匹配: {item['scores']['feature_match']:.4f}\n")
                f.write(f"  - 深度学习: {item['scores']['deep_learning']:.4f}\n")
                f.write(f"\nPrompt内容:\n{item['prompt']}\n\n")
                f.write("-"*80 + "\n\n")
        
        # 保存进度
        save_progress(arxiv_id, output_dir)
        
        return {
            'paper': paper,
            'arxiv_id': arxiv_id,
            'original_image': result_dir / "original.png",
            'prompts': [item['prompt'] for item in similarity_scores],
            'generated_images': [result_dir / f"generated_{i+1}.png" for i in range(len(generated_paths))],
            'similarity_scores': similarity_scores
        }
        
    except Exception as e:
        logger.error(f"处理论文 {arxiv_id} 时出错: {e}", exc_info=True)
        return None


def main():
    parser = argparse.ArgumentParser(description='图片Prompt测试脚本 - 优化版本')
    parser.add_argument('--num-images', type=int, default=100, help='要收集的流程图数量')
    parser.add_argument('--year', type=int, default=2024, help='论文年份')
    parser.add_argument('--openrouter-api-key', type=str, required=True, help='OpenRouter API密钥')
    parser.add_argument('--num-prompts', type=int, default=5, help='每个原图生成的prompt数量')
    parser.add_argument('--output-dir', type=str, default='data/prompt_test', help='输出目录')
    parser.add_argument('--max-papers', type=int, default=500, help='最多处理的论文数量')
    parser.add_argument('--parallel-papers', type=int, default=3, help='并行处理的论文数')
    parser.add_argument('--parallel-images', type=int, default=3, help='并行生成的图片数')
    parser.add_argument('--parallel-eval', type=int, default=5, help='并行评估的图片数')
    
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("图片Prompt测试脚本 - 优化版本")
    logger.info("="*80)
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载进度
    global processed_papers, progress_file
    progress_file = output_dir / ".progress"
    processed_papers = load_progress(output_dir)
    logger.info(f"已加载进度: {len(processed_papers)} 篇论文已处理")
    
    # 初始化
    db = Database(str(DB_PATH))
    api_client = OpenRouterClient(args.openrouter_api_key)
    evaluator = ImageSimilarityEvaluator()
    
    # 收集论文
    logger.info("步骤1: 收集论文标题")
    from scripts.image_prompt_test import collect_papers_from_multiple_categories
    collect_papers_from_multiple_categories(db, args.max_papers, args.year)
    
    # 获取待处理论文
    logger.info("步骤2: 获取待处理论文")
    to_download_papers = db.get_papers_by_status('pendingTitles')[:args.max_papers]
    logger.info(f"找到 {len(to_download_papers)} 篇待处理论文")
    
    # 并行处理论文
    logger.info("步骤3: 并行处理论文")
    results = []
    images_collected = len(processed_papers)  # 从已处理的开始计数
    
    with ThreadPoolExecutor(max_workers=args.parallel_papers) as executor:
        futures = {executor.submit(process_single_paper, paper, args, db, api_client, 
                                   output_dir, evaluator): paper for paper in to_download_papers}
        
        for future in as_completed(futures):
            if images_collected >= args.num_images:
                # 取消剩余任务
                for f in futures:
                    f.cancel()
                break
            
            result = future.result()
            if result:
                results.append(result)
                images_collected += 1
                logger.info(f"✓ 成功处理第 {images_collected}/{args.num_images} 张流程图")
    
    # 生成精选结果和总结报告
    logger.info("步骤4: 生成精选结果和总结报告")
    curated_dir = output_dir / "curated_results"
    curated_dir.mkdir(parents=True, exist_ok=True)
    
    for result in results:
        arxiv_id = result['arxiv_id']
        if result.get('similarity_scores') and len(result['similarity_scores']) > 0:
            best_result = result['similarity_scores'][0]
            paper_curated_dir = curated_dir / arxiv_id
            paper_curated_dir.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy2(result['original_image'], paper_curated_dir / "original.png")
            shutil.copy2(result['generated_images'][0], paper_curated_dir / "generated_best.png")
            
            best_prompt_file = paper_curated_dir / "best_prompt.txt"
            with open(best_prompt_file, 'w', encoding='utf-8') as f:
                f.write(f"论文: {result['paper']['title']}\n")
                f.write(f"来源: {result['paper'].get('source', 'N/A')}\n")
                f.write(f"arXiv ID: {arxiv_id}\n")
                f.write(f"相似度得分: {best_result['weighted_score']:.4f}\n")
                f.write(f"  - SSIM: {best_result['scores']['ssim']:.4f}\n")
                f.write(f"  - 特征匹配: {best_result['scores']['feature_match']:.4f}\n")
                f.write(f"  - 深度学习: {best_result['scores']['deep_learning']:.4f}\n")
                f.write("="*80 + "\n\n")
                f.write("最佳Prompt:\n")
                f.write(best_result['prompt'])
    
    # 生成总结报告
    summary_file = output_dir / "summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("图片Prompt测试总结报告（优化版本）\n")
        f.write("="*80 + "\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"目标图片数: {args.num_images}\n")
        f.write(f"实际收集图片数: {len(results)}\n")
        f.write(f"并行处理论文数: {args.parallel_papers}\n")
        f.write(f"并行生成图片数: {args.parallel_images}\n")
        f.write(f"并行评估数: {args.parallel_eval}\n\n")
        
        if results:
            avg_scores = []
            for result in results:
                if result.get('similarity_scores') and len(result['similarity_scores']) > 0:
                    avg_scores.append(result['similarity_scores'][0]['weighted_score'])
            
            if avg_scores:
                f.write(f"平均最佳相似度得分: {sum(avg_scores) / len(avg_scores):.4f}\n")
                f.write(f"最高相似度得分: {max(avg_scores):.4f}\n")
                f.write(f"最低相似度得分: {min(avg_scores):.4f}\n\n")
    
    logger.info("="*80)
    logger.info(f"完成！")
    logger.info(f"  收集了 {len(results)} 张流程图")
    logger.info(f"  输出目录: {output_dir}")
    logger.info(f"  精选结果: {output_dir}/curated_results/")
    logger.info("="*80)


if __name__ == '__main__':
    main()
