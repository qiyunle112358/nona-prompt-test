"""
图片Prompt测试脚本 - 完整流程
1. 筛选特定年份的论文并下载
2. 筛选论文中的流程图/演示图并下载
3. 根据原图生成5套prompt并生成对应图片
4. 整理输出文件夹
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
    'cs.CV',  # 计算机视觉
    'cs.CL',  # 自然语言处理
    'cs.LG',  # 机器学习
    'cs.AI',  # 人工智能
    'cs.RO',  # 机器人学
    'cs.GR',  # 图形学
    'physics.optics',  # 光学
    'physics.med-ph',  # 医学物理
    'q-bio.BM',  # 生物分子
    'math.OC',  # 优化与控制
    'stat.ML',  # 统计机器学习
    'eess.IV',  # 图像与视频处理
]

# 前置prompt（用于生图）
IMAGE_GENERATION_PREFIX = """You are an expert scientific illustrator and data visualization specialist for high-impact academic journals (e.g., IEEE, Nature, Springer).

Your Goal: Translate technical concepts, data, requirements, or architectures provided by the user into high-quality, publication-ready visualization images

Interaction Protocol: When the user provides a request, strictly follow their specified object description and constraints to generate the corresponding visual representation

**IMPORTANT**: Generate at least one image.

Context Explanation: I have provided you with the context of the project files currently being used by the user. You can use this as a reference, but the user's input should be taken as the primary reference./////////////"""


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
        """重试机制（指数退避）"""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                logger.warning(f"请求失败，{wait_time}秒后重试 (尝试 {attempt+1}/{self.max_retries}): {e}")
                time.sleep(wait_time)
        return None
    
    def image_to_text(self, image_path: Path, num_prompts: int = 5) -> List[str]:
        """
        图生文：分析图片并生成prompt
        
        Args:
            image_path: 图片路径
            num_prompts: 生成prompt的数量
            
        Returns:
            prompt列表
        """
        try:
            # 读取图片并编码为base64
            with open(image_path, 'rb') as f:
                image_data = f.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # 确定MIME类型
            ext = image_path.suffix.lower()
            mime_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            mime_type = mime_types.get(ext, 'image/png')
            image_url = f"data:{mime_type};base64,{image_base64}"
            
            # 构建prompt，要求生成超级详细、超长的prompt
            prompt_text = f"""Analyze this scientific/academic diagram/flowchart image with EXTREME attention to detail and generate exactly {num_prompts} different ULTRA-DETAILED prompts that could be used to recreate an image as IDENTICAL as possible to the original.

CRITICAL REQUIREMENTS:
- Return ONLY the {num_prompts} prompts, nothing else
- Start directly with "1." followed by the first prompt
- Do NOT include any introductory text like "Here are...", "The following...", etc.
- Each prompt should be on a separate line, numbered as "1.", "2.", "3.", etc.
- Use a blank line between each prompt for clarity
- PROMPT LENGTH: Each prompt should be EXTREMELY LONG (500-2000+ words) - describe EVERY SINGLE DETAIL

Each prompt MUST be ULTRA-DETAILED and describe ABSOLUTELY EVERY aspect of the image in extreme detail:

1. **Layout and Structure** (describe in detail):
   - Exact positioning of every element (coordinates, alignment, relative positions)
   - Overall layout structure (grid, hierarchical, flow, etc.)
   - Spacing between all elements (exact distances in pixels or relative units)
   - Margins and padding for every component
   - Alignment of all elements (left, right, center, justified)

2. **Visual Elements** (describe EVERY element):
   - Every shape, box, circle, rectangle, polygon - their exact positions, sizes, dimensions
   - Every arrow, line, connector - their exact paths, start/end points, curves, angles
   - Every icon, symbol, graphic element - their exact appearance and position
   - Exact sizes of all elements (width, height in pixels or relative units)
   - Exact orientations and rotations of all elements

3. **Text and Labels** (describe EVERY text element):
   - ALL text content - every word, number, symbol, character
   - Exact positions of all text elements
   - Font family, size, weight, style for each text element
   - Text alignment and justification
   - Text colors for each element
   - Text background colors or highlights
   - Text spacing (letter-spacing, line-height)

4. **Colors** (describe EVERY color):
   - Exact color for every element (use specific color names or hex codes like #FF5733)
   - Fill colors for all shapes
   - Border/outline colors for all elements
   - Text colors for all labels
   - Background colors for different regions
   - Gradient colors (if any) with exact color stops
   - Transparency/opacity values for each element

5. **Connections and Relationships** (describe EVERY connection):
   - Every arrow, line, connector - their exact paths
   - Start and end points of all connections
   - Connection styles (solid, dashed, dotted, etc.)
   - Arrow styles (arrowhead shape, size, direction)
   - Line thickness for each connection
   - Curvature and angles of all curved connections
   - Which elements connect to which (exact relationships)

6. **Styling Details** (describe EVERY style):
   - Line thickness for every line, border, outline
   - Border styles (solid, dashed, dotted, double, etc.)
   - Fill patterns (solid, gradient, pattern, texture)
   - Shadow effects (if any) - offset, blur, color, opacity
   - Gradient effects - direction, colors, stops
   - Rounded corners - exact radius for each element
   - 3D effects, depth, perspective (if any)

7. **Spacing and Dimensions** (exact measurements):
   - Exact distances between all elements
   - Margins around every component
   - Padding inside every container
   - Overall dimensions of the entire diagram
   - Aspect ratios of all elements

8. **Background** (detailed description):
   - Background color or pattern
   - Background texture or gradient
   - Transparency level
   - Any background images or watermarks

9. **Typography** (for EVERY text element):
   - Font family (Arial, Times, Helvetica, etc.)
   - Font size (exact point size or pixels)
   - Font weight (normal, bold, light, etc.)
   - Font style (normal, italic, oblique)
   - Text decoration (underline, strikethrough, etc.)
   - Text transform (uppercase, lowercase, capitalize)

10. **Overall Style and Context**:
    - Scientific diagram style characteristics
    - Academic paper style conventions
    - Visual hierarchy and emphasis
    - Color scheme and palette
    - Overall aesthetic and design principles

11. **Additional Details**:
    - Any annotations, callouts, or notes
    - Any legends, keys, or explanatory elements
    - Any grid lines, guides, or reference elements
    - Any decorative elements or embellishments
    - Any data visualizations (charts, graphs) embedded in the diagram

IMPORTANT: 
- Be EXTREMELY VERBOSE - describe every single pixel-level detail you can observe
- Use precise measurements and coordinates when possible
- Mention every color, every shape, every text element
- Describe relationships and connections in detail
- The prompt should be LONG (500-2000+ words per prompt) - don't worry about length
- The goal is to create prompts so detailed that the generated image will be pixel-perfect identical to the original

Format:
1. [First ULTRA-DETAILED prompt - 500-2000+ words describing every detail]
2. [Second ULTRA-DETAILED prompt - 500-2000+ words describing every detail]
3. [Third ULTRA-DETAILED prompt - 500-2000+ words describing every detail]
4. [Fourth ULTRA-DETAILED prompt - 500-2000+ words describing every detail]
5. [Fifth ULTRA-DETAILED prompt - 500-2000+ words describing every detail]"""

            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": "google/gemini-2.5-flash",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt_text
                            }
                        ]
                    }
                ]
            }
            
            logger.info(f"调用OpenRouter API分析图片: {image_path.name}")
            
            def make_request():
                response = requests.post(url, headers=self.headers, json=payload, timeout=120)
                if response.status_code != 200:
                    raise Exception(f"API请求失败: {response.status_code} - {response.text}")
                return response.json()
            
            result = self._retry_request(make_request)
            if not result:
                return []
            
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"].strip()
                
                # 解析返回的prompt列表
                prompts = []
                
                # 移除常见的总指令文本（更全面的列表）
                skip_patterns = [
                    "here are",
                    "here are 5",
                    "here are 5 detailed prompts",
                    "here are 5 detailed prompts that could be used",
                    "the following",
                    "below are",
                    "i'll provide",
                    "i will provide",
                    "these prompts",
                    "the prompts",
                    "detailed prompts that could be used",
                    "prompts to recreate",
                    "focusing on",
                    "clarity, structure",
                    "scientific visualization style",
                    "以下是",
                    "下面是",
                    "我将提供",
                    "这些提示",
                    "each prompt should",
                    "return the prompts",
                    "format:",
                    "important:",
                    "note:",
                    "提示：",
                    "注意："
                ]
                
                # 检查是否是总指令文本的特征
                def is_instruction_text(text):
                    text_lower = text.lower().strip()
                    # 如果文本很短（<150字符）且包含指令关键词，很可能是总指令
                    if len(text) < 150:
                        for pattern in skip_patterns:
                            if pattern in text_lower:
                                return True
                    # 如果文本以"here are"、"the following"等开头，很可能是总指令
                    instruction_starters = ["here are", "the following", "below are", "i'll provide", 
                                           "i will provide", "these prompts", "以下是", "下面是"]
                    for starter in instruction_starters:
                        if text_lower.startswith(starter):
                            return True
                    return False
                
                # 首先尝试按编号分割（更可靠的方法）
                # 查找所有以数字开头的行（如 "1.", "2.", "3."等）
                lines = content.split('\n')
                current_prompt_parts = []
                current_number = None
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        # 空行：如果当前有prompt内容，保存它
                        if current_prompt_parts and current_number is not None:
                            full_prompt = ' '.join(current_prompt_parts).strip()
                            if len(full_prompt) > 50 and not is_instruction_text(full_prompt):
                                # 移除编号前缀
                                for prefix in ['prompt 1:', 'prompt 2:', 'prompt 3:', 'prompt 4:', 'prompt 5:',
                                               '1.', '2.', '3.', '4.', '5.']:
                                    if full_prompt.lower().startswith(prefix.lower()):
                                        full_prompt = full_prompt[len(prefix):].strip()
                                        if full_prompt.startswith(':'):
                                            full_prompt = full_prompt[1:].strip()
                                        break
                                if full_prompt not in prompts:
                                    prompts.append(full_prompt)
                            current_prompt_parts = []
                            current_number = None
                        continue
                    
                    # 检查是否是新的prompt开始（以数字编号开头）
                    line_lower = line.lower()
                    is_new_prompt = False
                    for i in range(1, 10):
                        prefix = f"{i}."
                        if line_lower.startswith(prefix) or line_lower.startswith(f"prompt {i}:"):
                            # 保存之前的prompt
                            if current_prompt_parts and current_number is not None:
                                full_prompt = ' '.join(current_prompt_parts).strip()
                                if len(full_prompt) > 50 and not is_instruction_text(full_prompt):
                                    # 移除编号前缀
                                    for prefix_old in ['prompt 1:', 'prompt 2:', 'prompt 3:', 'prompt 4:', 'prompt 5:',
                                                       '1.', '2.', '3.', '4.', '5.']:
                                        if full_prompt.lower().startswith(prefix_old.lower()):
                                            full_prompt = full_prompt[len(prefix_old):].strip()
                                            if full_prompt.startswith(':'):
                                                full_prompt = full_prompt[1:].strip()
                                            break
                                    if full_prompt not in prompts:
                                        prompts.append(full_prompt)
                            
                            # 开始新的prompt
                            current_number = i
                            # 移除编号，保留内容
                            for prefix_remove in [f"{i}.", f"prompt {i}:", f"**prompt {i}"]:
                                if line_lower.startswith(prefix_remove.lower()):
                                    line = line[len(prefix_remove):].strip()
                                    if line.startswith(':'):
                                        line = line[1:].strip()
                                    break
                            current_prompt_parts = [line] if line else []
                            is_new_prompt = True
                            break
                    
                    if not is_new_prompt:
                        # 继续当前prompt
                        if current_number is not None:
                            current_prompt_parts.append(line)
                        elif not is_instruction_text(line):
                            # 如果还没有开始编号，但这一行不是指令，可能是第一个prompt的开始
                            # 检查是否包含prompt特征（描述性文本）
                            if len(line) > 50 and any(word in line_lower for word in ['create', 'design', 'generate', 'produce', 'construct', 'visualize']):
                                current_number = 1
                                current_prompt_parts = [line]
                
                # 处理最后一个prompt
                if current_prompt_parts and current_number is not None:
                    full_prompt = ' '.join(current_prompt_parts).strip()
                    if len(full_prompt) > 50 and not is_instruction_text(full_prompt):
                        # 移除编号前缀
                        for prefix in ['prompt 1:', 'prompt 2:', 'prompt 3:', 'prompt 4:', 'prompt 5:',
                                       '1.', '2.', '3.', '4.', '5.']:
                            if full_prompt.lower().startswith(prefix.lower()):
                                full_prompt = full_prompt[len(prefix):].strip()
                                if full_prompt.startswith(':'):
                                    full_prompt = full_prompt[1:].strip()
                                break
                        if full_prompt not in prompts:
                            prompts.append(full_prompt)
                
                # 如果按编号分割没有找到足够的prompt，回退到按段落分割
                if len(prompts) < num_prompts:
                    logger.debug("按编号分割prompt数量不足，尝试按段落分割...")
                    paragraphs = content.split('\n\n')
                    
                    for para in paragraphs:
                        para = para.strip()
                        if not para or len(para) < 30:
                            continue
                        
                        if is_instruction_text(para):
                            continue
                        
                        # 移除编号前缀
                        para_lower = para.lower()
                        for prefix in ['prompt 1:', 'prompt 2:', 'prompt 3:', 'prompt 4:', 'prompt 5:',
                                       '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.',
                                       '-', '*', '•', '**prompt', '**prompt 1', '**prompt 2']:
                            if para_lower.startswith(prefix.lower()):
                                para = para[len(prefix):].strip()
                                if para.startswith(':'):
                                    para = para[1:].strip()
                                break
                        
                        para = para.strip('"\'')
                        
                        if len(para) > 50 and para not in prompts and not is_instruction_text(para):
                            prompts.append(para)
                
                # 如果按段落分割不够，尝试按行分割
                if len(prompts) < num_prompts:
                    lines = content.split('\n')
                    current_prompt = ""
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            if current_prompt and len(current_prompt) > 50:
                                if not is_instruction_text(current_prompt):
                                    if current_prompt not in prompts:
                                        prompts.append(current_prompt)
                            current_prompt = ""
                            continue
                        
                        # 检查是否是新的prompt开始（包含编号）
                        is_new_prompt = False
                        for prefix in ['prompt', '1.', '2.', '3.', '4.', '5.']:
                            if line.lower().startswith(prefix.lower()):
                                if current_prompt and len(current_prompt) > 50:
                                    if not is_instruction_text(current_prompt):
                                        if current_prompt not in prompts:
                                            prompts.append(current_prompt)
                                current_prompt = line
                                is_new_prompt = True
                                break
                        
                        if not is_new_prompt:
                            if current_prompt:
                                current_prompt += " " + line
                            else:
                                current_prompt = line
                    
                    # 处理最后一个prompt
                    if current_prompt and len(current_prompt) > 50:
                        if not is_instruction_text(current_prompt):
                            if current_prompt not in prompts:
                                prompts.append(current_prompt)
                
                # 清理prompt：移除编号和多余空白
                cleaned_prompts = []
                for prompt in prompts:
                    # 移除开头的编号
                    prompt = prompt.strip()
                    for prefix in ['prompt 1:', 'prompt 2:', 'prompt 3:', 'prompt 4:', 'prompt 5:',
                                   '1.', '2.', '3.', '4.', '5.', '-', '*', '**']:
                        if prompt.lower().startswith(prefix.lower()):
                            prompt = prompt[len(prefix):].strip()
                            if prompt.startswith(':'):
                                prompt = prompt[1:].strip()
                            break
                    
                    # 移除引号
                    prompt = prompt.strip('"\'')
                    
                    # 确保prompt有足够内容
                    if len(prompt) > 50:
                        cleaned_prompts.append(prompt)
                
                prompts = cleaned_prompts
                
                # 确保返回指定数量的prompt
                if len(prompts) > num_prompts:
                    prompts = prompts[:num_prompts]
                elif len(prompts) < num_prompts:
                    # 如果不够，尝试从原始内容中提取更多
                    logger.warning(f"只提取到 {len(prompts)} 个prompt，需要 {num_prompts} 个")
                    # 如果还是不够，使用占位符
                    while len(prompts) < num_prompts:
                        if prompts:
                            prompts.append(prompts[-1] + " (variation)")
                        else:
                            prompts.append("A detailed scientific diagram visualization")
                
                logger.info(f"✓ 成功生成 {len(prompts)} 个prompt")
                # 记录前两个prompt的前50个字符用于调试
                for i, p in enumerate(prompts[:2], 1):
                    logger.debug(f"Prompt {i} 预览: {p[:80]}...")
                
                return prompts
            else:
                logger.warning("API响应中未找到内容")
                return []
                
        except Exception as e:
            logger.error(f"分析图片时出错 {image_path}: {e}")
            return []
    
    def text_to_image(self, prompt: str, output_path: Path) -> bool:
        """
        文生图：根据prompt生成图片
        
        Args:
            prompt: 生成prompt
            output_path: 输出路径
            
        Returns:
            是否成功
        """
        try:
            # 组合前置prompt和用户prompt
            full_prompt = f"{IMAGE_GENERATION_PREFIX}\n\n{prompt}"
            
            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": "google/gemini-3-pro-image-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": full_prompt
                            }
                        ]
                    }
                ],
                "modalities": ["image", "text"]
            }
            
            logger.info(f"调用OpenRouter API生成图片...")
            
            def make_request():
                response = requests.post(url, headers=self.headers, json=payload, timeout=600)
                if response.status_code != 200:
                    raise Exception(f"API请求失败: {response.status_code} - {response.text}")
                return response.json()
            
            result = self._retry_request(make_request)
            if not result:
                return False
            
            # 提取生成的图像
            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0]["message"]
                
                if message.get("images"):
                    # 获取第一张图片
                    image_url = message["images"][0]["image_url"]["url"]
                    
                    # 提取base64数据
                    if "base64," in image_url:
                        base64_data = image_url.split("base64,")[1]
                        image_bytes = base64.b64decode(base64_data)
                        
                        # 保存图片
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, "wb") as f:
                            f.write(image_bytes)
                        
                        logger.info(f"✓ 图片已保存: {output_path.name}")
                        return True
                    else:
                        logger.warning("响应中未找到base64图片数据")
                        return False
                else:
                    logger.warning("响应中未找到生成的图片")
                    return False
            else:
                logger.warning("API响应格式异常")
                return False
                
        except Exception as e:
            logger.error(f"生成图片时出错 {prompt[:50]}...: {e}")
            return False


class FlowchartExtractor:
    """从PDF中提取流程图/演示图（基于关键词搜索）"""
    
    # 关键词列表（中文及其英文对应，严格按照用户要求）
    KEYWORDS = [
        # 中文关键词
        '流程图', '技术路线', '框架图', '实验设计', '工作流程', '架构图',
        # 对应的英文关键词
        'Flowchart', 'Technical Roadmap', 'Framework Diagram', 'Experimental Design', 
        'Workflow', 'Architecture Diagram', 'Architecture'
    ]
    
    def __init__(self, pdf_path: Path, output_dir: Path):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def search_keywords_in_pdf(self, doc) -> List[Dict]:
        """
        在PDF中搜索关键词，返回包含关键词的页面和位置信息
        搜索中文关键词及其对应的英文关键词
        
        Returns:
            包含关键词的页面列表，每个元素包含 {page_num, text, keyword}
        """
        keyword_matches = []
        
        # 中文关键词及其英文对应（严格按照用户要求）
        keyword_pairs = [
            ('流程图', 'Flowchart'),
            ('技术路线', 'Technical Roadmap'),
            ('框架图', 'Framework Diagram'),
            ('实验设计', 'Experimental Design'),
            ('工作流程', 'Workflow'),
            ('架构图', 'Architecture Diagram')
        ]
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            text_lower = text.lower()
            
            # 搜索中文关键词及其英文对应
            for chinese_keyword, english_keyword in keyword_pairs:
                found = False
                matched_keyword = None
                
                # 先搜索中文关键词
                if chinese_keyword in text:
                    found = True
                    matched_keyword = chinese_keyword
                # 再搜索对应的英文关键词
                elif english_keyword.lower() in text_lower:
                    found = True
                    matched_keyword = english_keyword
                # 不搜索其他变体，严格按照指定的关键词
                
                if found:
                    # 获取关键词周围的文本上下文
                    keyword_index = text_lower.find(matched_keyword.lower())
                    start = max(0, keyword_index - 100)
                    end = min(len(text), keyword_index + len(matched_keyword) + 100)
                    context = text[start:end]
                    
                    keyword_matches.append({
                        'page_num': page_num,
                        'keyword': matched_keyword,
                        'context': context
                    })
                    logger.info(f"在第{page_num+1}页找到关键词: {matched_keyword}")
                    break  # 找到关键词后，跳出循环，继续下一页
        
        return keyword_matches
    
    def extract_image_near_keyword(self, doc, page_num: int, keyword: str) -> Optional[Path]:
        """
        基于坐标定位提取关键词附近的图片（改进版）
        
        Args:
            doc: PDF文档对象
            page_num: 页面编号
            keyword: 关键词
            
        Returns:
            提取的图片路径，如果没有找到返回None
        """
        try:
            page = doc[page_num]
            
            # 1. 获取关键词在页面上的位置（坐标）
            keyword_instances = page.search_for(keyword)
            
            if not keyword_instances:
                logger.debug(f"页面{page_num+1}上未找到关键词'{keyword}'的坐标位置")
                # 降级到原来的方法：提取页面第一张符合条件的图片
                return self._extract_first_valid_image(doc, page_num, keyword)
            
            # 2. 获取页面上所有图片及其位置
            image_list = page.get_images()
            if not image_list:
                return None
            
            image_rects = []
            for img_index, img in enumerate(image_list):
                xref = img[0]
                try:
                    # 获取图片在页面上的位置（矩形区域）
                    img_rects = page.get_image_rects(xref)
                    for rect in img_rects:
                        image_rects.append({
                            'rect': rect,
                            'index': img_index,
                            'xref': xref
                        })
                except Exception as e:
                    logger.debug(f"无法获取图片{img_index}的位置: {e}")
                    continue
            
            if not image_rects:
                logger.debug(f"页面{page_num+1}上未找到图片位置信息")
                # 降级到原来的方法
                return self._extract_first_valid_image(doc, page_num, keyword)
            
            # 3. 找到距离关键词最近的图片
            best_image = None
            min_distance = float('inf')
            
            for keyword_rect in keyword_instances:
                keyword_center = (
                    (keyword_rect.x0 + keyword_rect.x1) / 2,
                    (keyword_rect.y0 + keyword_rect.y1) / 2
                )
                
                for img_info in image_rects:
                    img_rect = img_info['rect']
                    img_center = (
                        (img_rect.x0 + img_rect.x1) / 2,
                        (img_rect.y0 + img_rect.y1) / 2
                    )
                    
                    # 计算欧氏距离
                    distance = ((keyword_center[0] - img_center[0])**2 + 
                               (keyword_center[1] - img_center[1])**2)**0.5
                    
                    if distance < min_distance:
                        min_distance = distance
                        best_image = img_info
            
            # 4. 提取最近的图片（距离阈值：1000像素，约等于页面高度的1.5倍）
            if best_image and min_distance < 1000:
                try:
                    base_image = doc.extract_image(best_image['xref'])
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    filename = f"diagram_page_{page_num}_img_{best_image['index']}.{image_ext}"
                    image_path = self.output_dir / filename
                    
                    with open(image_path, "wb") as img_file:
                        img_file.write(image_bytes)
                    
                    # 检查图片尺寸
                    try:
                        img_pil = Image.open(image_path)
                        width, height = img_pil.size
                        if width >= 200 and height >= 200:
                            logger.info(f"提取图片: {filename} (关键词: {keyword}, 页面: {page_num+1}, 距离: {min_distance:.1f}px)")
                            return image_path
                        else:
                            image_path.unlink()
                    except Exception:
                        if image_path.exists():
                            image_path.unlink()
                except Exception as e:
                    logger.warning(f"提取最近图片时出错: {e}")
            
            # 如果基于坐标的方法失败，降级到原来的方法
            logger.debug(f"基于坐标定位失败，使用降级方法")
            return self._extract_first_valid_image(doc, page_num, keyword)
            
        except Exception as e:
            logger.error(f"提取图片时出错 (页面{page_num+1}): {e}")
            # 降级到原来的方法
            return self._extract_first_valid_image(doc, page_num, keyword)
    
    def _extract_first_valid_image(self, doc, page_num: int, keyword: str) -> Optional[Path]:
        """
        降级方法：提取页面第一张符合条件的图片（原来的实现）
        """
        try:
            page = doc[page_num]
            image_list = page.get_images()
            
            if not image_list:
                return None
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                filename = f"diagram_page_{page_num}_img_{img_index}.{image_ext}"
                image_path = self.output_dir / filename
                
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)
                
                try:
                    img_pil = Image.open(image_path)
                    width, height = img_pil.size
                    if width >= 200 and height >= 200:
                        logger.info(f"提取图片: {filename} (关键词: {keyword}, 页面: {page_num+1}, 降级方法)")
                        return image_path
                    else:
                        image_path.unlink()
                except Exception:
                    if image_path.exists():
                        image_path.unlink()
            
            return None
        except Exception as e:
            logger.error(f"降级方法提取图片时出错: {e}")
            return None
    
    def extract_flowchart(self) -> Optional[Path]:
        """
        从PDF中提取一张流程图/演示图
        通过搜索关键词找到对应的图片
        
        Returns:
            提取的图片路径，如果没有找到返回None
        """
        try:
            doc = fitz.open(self.pdf_path)
            
            # 1. 搜索关键词
            keyword_matches = self.search_keywords_in_pdf(doc)
            
            if not keyword_matches:
                doc.close()
                logger.warning(f"PDF {self.pdf_path.name} 中未找到关键词，跳过此论文")
                return None
            
            logger.info(f"在PDF中找到 {len(keyword_matches)} 个关键词匹配")
            
            if not keyword_matches:
                doc.close()
                logger.warning(f"PDF {self.pdf_path.name} 中未找到关键词（流程图、技术路线、框架图、实验设计、工作流程、架构图），跳过此论文")
                return None
            
            # 2. 按优先级提取图片（优先选择包含流程图、架构图、工作流程等关键词的页面）
            priority_keywords = ['流程图', 'Flowchart', '架构图', 'Architecture', '工作流程', 'Workflow', 
                               '技术路线', 'Technical Roadmap', '框架图', 'Framework']
            
            # 先尝试优先级高的关键词
            for priority_kw in priority_keywords:
                for match in keyword_matches:
                    if priority_kw.lower() in match['keyword'].lower():
                        image_path = self.extract_image_near_keyword(
                            doc, match['page_num'], match['keyword']
                        )
                        if image_path:
                            doc.close()
                            logger.info(f"成功提取流程图: {image_path.name} (基于关键词: {match['keyword']})")
                            return image_path
            
            # 如果没有找到，尝试其他关键词
            for match in keyword_matches:
                image_path = self.extract_image_near_keyword(
                    doc, match['page_num'], match['keyword']
                )
                if image_path:
                    doc.close()
                    logger.info(f"成功提取流程图: {image_path.name} (基于关键词: {match['keyword']})")
                    return image_path
            
            doc.close()
            logger.warning(f"PDF {self.pdf_path.name} 中找到了关键词但未找到对应的图片")
            return None
                
        except Exception as e:
            logger.error(f"提取流程图时出错 {self.pdf_path}: {e}")
            return None


def collect_papers_from_multiple_categories(db: Database, num_papers: int = 100, year: int = 2024):
    """从多个领域收集论文"""
    papers_collected = 0
    papers_per_category = max(1, num_papers // len(ARXIV_CATEGORIES))
    
    logger.info(f"开始从 {len(ARXIV_CATEGORIES)} 个领域收集 {num_papers} 篇论文")
    
    for category in ARXIV_CATEGORIES:
        if papers_collected >= num_papers:
            break
        
        try:
            logger.info(f"收集 {category} 领域的论文...")
            papers = collectors.collect_arxiv_papers(
                year=year,
                category=category,
                max_results=papers_per_category + 10
            )
            
            # 保存到数据库
            for paper in papers[:papers_per_category]:
                if papers_collected >= num_papers:
                    break
                
                db.insert_paper({
                    'title': paper['title'],
                    'source': f'arXiv{year}_{category}',
                    'published_date': paper.get('published_date', ''),
                    'status': 'pendingTitles'
                })
                papers_collected += 1
            
            logger.info(f"已收集 {papers_collected} 篇论文")
            
        except Exception as e:
            logger.error(f"收集 {category} 领域论文时出错: {e}")
            continue
    
    logger.info(f"总共收集了 {papers_collected} 篇论文")
    return papers_collected


def main():
    parser = argparse.ArgumentParser(description='图片Prompt测试脚本 - 完整流程（优化版）')
    parser.add_argument('--num-images', type=int, default=100, help='要收集的流程图数量（默认100）')
    parser.add_argument('--year', type=int, default=2024, help='论文年份（默认2024）')
    parser.add_argument('--openrouter-api-key', type=str, required=True, help='OpenRouter API密钥')
    parser.add_argument('--num-prompts', type=int, default=5, help='每个原图生成的prompt数量（默认5）')
    parser.add_argument('--output-dir', type=str, default='data/prompt_test', help='输出目录')
    parser.add_argument('--max-papers', type=int, default=500, help='最多处理的论文数量（默认500）')
    parser.add_argument('--parallel-images', type=int, default=3, help='并行生成图片数（默认3，避免API限流）')
    parser.add_argument('--parallel-eval', type=int, default=5, help='并行评估相似度数（默认5）')
    parser.add_argument('--resume', action='store_true', help='从上次中断处继续')
    
    args = parser.parse_args()
    
    logger.info("="*80)
    logger.info("图片Prompt测试脚本 - 完整流程")
    logger.info("="*80)
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 初始化数据库和API客户端
    db = Database(str(DB_PATH))
    api_client = OpenRouterClient(args.openrouter_api_key)
    
    # 加载已处理的论文（断点续传）
    processed_arxiv_ids = set()
    progress_file = output_dir / ".progress"
    if args.resume:
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                processed_arxiv_ids = set(line.strip() for line in f if line.strip())
            logger.info(f"从进度文件加载: {len(processed_arxiv_ids)} 篇论文已处理")
        
        # 检查是否需要收集更多论文
        to_download_count = len(db.get_papers_by_status('TobeDownloaded', limit=1000))
        pending_count = len(db.get_papers_by_status('pendingTitles', limit=1000))
        total_available = to_download_count + pending_count
        
        if total_available < (args.num_images - len(processed_arxiv_ids)):
            logger.warning(f"可用论文数 ({total_available}) 可能不足以达到目标 ({args.num_images - len(processed_arxiv_ids)} 张)，将执行步骤1和步骤2收集更多论文")
            # 需要收集更多论文
            need_more_papers = True
        else:
            logger.info("使用 --resume 模式，跳过步骤1和步骤2，直接进入步骤3")
            need_more_papers = False
    else:
        need_more_papers = True
    
    # 步骤1: 收集论文（如果需要）
    if need_more_papers:
        logger.info("\n" + "="*80)
        logger.info("步骤1: 收集论文标题")
        logger.info("="*80)
        collect_papers_from_multiple_categories(db, args.max_papers, args.year)
        
        # 步骤2: 获取论文详细信息
        logger.info("\n" + "="*80)
        logger.info("步骤2: 获取论文详细信息")
        logger.info("="*80)
        
        pending_papers = db.get_papers_by_status('pendingTitles', limit=args.max_papers)
        if pending_papers:
            from fetchers import fetch_paper_info
            for i, paper in enumerate(pending_papers, 1):
                logger.info(f"获取论文信息 {i}/{len(pending_papers)}: {paper['title'][:50]}...")
                info = fetch_paper_info(paper['title'])
                if info:
                    db.update_paper_info(paper['id'], {
                        'arxiv_id': info.get('arxiv_id'),
                        'pdf_url': info.get('pdf_url'),
                        'authors': info.get('authors', []),
                        'abstract': info.get('abstract'),
                        'status': 'TobeDownloaded'
                    })
    else:
        logger.info("\n" + "="*80)
        logger.info("步骤1和步骤2: 已跳过（使用 --resume 模式，有足够的待处理论文）")
        logger.info("="*80)
    
    # 步骤3: 下载PDF并提取流程图
    logger.info("\n" + "="*80)
    logger.info("步骤3: 下载PDF并提取流程图")
    logger.info("="*80)
    
    to_download_papers = db.get_papers_by_status('TobeDownloaded', limit=args.max_papers)
    if not to_download_papers:
        logger.warning("没有待下载的论文")
        # 如果使用resume且已有进度，检查是否需要继续收集论文
        if args.resume and len(processed_arxiv_ids) > 0 and len(processed_arxiv_ids) < args.num_images:
            logger.warning(f"当前已处理 {len(processed_arxiv_ids)} 张图，目标 {args.num_images} 张，但数据库中没有更多待处理论文")
            logger.info("将自动执行步骤1和步骤2以收集更多论文...")
            # 自动收集更多论文
            collect_papers_from_multiple_categories(db, args.max_papers, args.year)
            pending_papers = db.get_papers_by_status('pendingTitles', limit=args.max_papers)
            if pending_papers:
                from fetchers import fetch_paper_info
                logger.info(f"获取 {len(pending_papers)} 篇论文的详细信息...")
                for i, paper in enumerate(pending_papers, 1):
                    logger.info(f"获取论文信息 {i}/{len(pending_papers)}: {paper['title'][:50]}...")
                    info = fetch_paper_info(paper['title'])
                    if info:
                        db.update_paper_info(paper['id'], {
                            'arxiv_id': info.get('arxiv_id'),
                            'pdf_url': info.get('pdf_url'),
                            'authors': info.get('authors', []),
                            'abstract': info.get('abstract'),
                            'status': 'TobeDownloaded'
                        })
            # 重新获取待下载论文
            to_download_papers = db.get_papers_by_status('TobeDownloaded', limit=args.max_papers)
            if not to_download_papers:
                logger.error("收集论文后仍然没有待下载的论文，退出")
                return
        else:
            return
    
    results = []
    # 从已处理的论文数开始计数（断点续传）
    images_collected = len(processed_arxiv_ids) if args.resume else 0
    papers_processed = 0
    
    # 保存进度文件
    progress_file = output_dir / ".progress"
    
    logger.info(f"当前进度: {images_collected}/{args.num_images} 张图（已处理 {len(processed_arxiv_ids)} 篇论文）")
    
    # 检查是否有未处理的论文
    unprocessed_papers = [p for p in to_download_papers 
                          if not (args.resume and p.get('arxiv_id') in processed_arxiv_ids)]
    
    if not unprocessed_papers and images_collected < args.num_images:
        logger.warning(f"所有待下载论文都已被处理，但还未达到目标 ({images_collected}/{args.num_images})")
        logger.info("自动收集更多论文...")
        # 收集更多论文
        collect_papers_from_multiple_categories(db, args.max_papers, args.year)
        # 获取论文信息
        pending_papers = db.get_papers_by_status('pendingTitles', limit=args.max_papers)
        if pending_papers:
            from fetchers import fetch_paper_info
            logger.info(f"获取 {len(pending_papers)} 篇论文的详细信息...")
            for i, paper in enumerate(pending_papers[:50], 1):  # 限制获取50篇，避免耗时过长
                logger.info(f"获取论文信息 {i}/{min(50, len(pending_papers))}: {paper['title'][:50]}...")
                info = fetch_paper_info(paper['title'])
                if info:
                    db.update_paper_info(paper['id'], {
                        'arxiv_id': info.get('arxiv_id'),
                        'pdf_url': info.get('pdf_url'),
                        'authors': info.get('authors', []),
                        'abstract': info.get('abstract'),
                        'status': 'TobeDownloaded'
                    })
        # 重新获取待下载论文
        to_download_papers = db.get_papers_by_status('TobeDownloaded', limit=args.max_papers)
        unprocessed_papers = [p for p in to_download_papers 
                              if not (args.resume and p.get('arxiv_id') in processed_arxiv_ids)]
        if not unprocessed_papers:
            logger.error("收集论文后仍然没有未处理的论文，退出")
            return
    
    for paper in to_download_papers:
        if images_collected >= args.num_images:
            logger.info(f"已达到目标数量 {args.num_images} 张图，停止处理")
            break
        
        arxiv_id = paper.get('arxiv_id')
        pdf_url = paper.get('pdf_url')
        
        if not arxiv_id or not pdf_url:
            continue
        
        # 检查是否已处理（断点续传）
        if args.resume and arxiv_id in processed_arxiv_ids:
            logger.info(f"跳过已处理的论文: {arxiv_id}")
            continue
        
        papers_processed += 1
        logger.info(f"\n处理论文 {papers_processed}: {paper['title'][:60]}...")
        
        # 下载PDF
        pdf_path = PDF_DIR / f"{arxiv_id}.pdf"
        if not pdf_path.exists():
            from processors import download_pdf
            logger.info(f"  下载PDF: {arxiv_id}")
            if not download_pdf(pdf_url, pdf_path):
                logger.warning(f"  PDF下载失败，跳过")
                continue
        
        # 提取流程图
        extractor = FlowchartExtractor(pdf_path, output_dir / "original_images" / arxiv_id)
        flowchart_path = extractor.extract_flowchart()
        
        if not flowchart_path:
            logger.warning(f"  未找到流程图，跳过此论文")
            # 删除此论文记录
            db.delete_paper(paper['id'])
            continue
        
        # 生成prompt
        logger.info(f"  生成prompt...")
        prompts = api_client.image_to_text(flowchart_path, args.num_prompts)
        
        if not prompts:
            logger.warning(f"  未能生成prompt，跳过")
            continue
        
        # 并行生成图片
        logger.info(f"  并行生成 {len(prompts)} 张图片...")
        gen_dir = output_dir / "generated_images" / arxiv_id
        gen_dir.mkdir(parents=True, exist_ok=True)
        
        def generate_image(i, prompt):
            gen_path = gen_dir / f"prompt_{i}.png"
            if api_client.text_to_image(prompt, gen_path):
                return (i, gen_path, prompt)
            return None
        
        generated_results = []
        with ThreadPoolExecutor(max_workers=args.parallel_images) as executor:
            futures = {executor.submit(generate_image, i+1, p): i for i, p in enumerate(prompts)}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    generated_results.append(result)
                    logger.info(f"    ✓ Prompt {result[0]} 图片已生成")
        
        # 按原始顺序排序
        generated_results.sort(key=lambda x: x[0])
        generated_paths = [r[1] for r in generated_results]
        generated_prompts = [r[2] for r in generated_results]
        
        if generated_paths:
            # 并行评估相似度并排名
            logger.info(f"  并行评估 {len(generated_paths)} 张图片的相似度...")
            evaluator = ImageSimilarityEvaluator()
            
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
            with ThreadPoolExecutor(max_workers=args.parallel_eval) as executor:
                futures = {executor.submit(evaluate_image, i, path): i for i, path in enumerate(generated_paths)}
                for future in as_completed(futures):
                    result = future.result()
                    similarity_scores.append(result)
                    logger.info(f"    Prompt {result['index']} 相似度: SSIM={result['scores']['ssim']:.3f}, "
                              f"特征匹配={result['scores']['feature_match']:.3f}, "
                              f"深度学习={result['scores']['deep_learning']:.3f}, "
                              f"加权得分={result['weighted_score']:.3f}")
            
            # 按加权得分排序（降序）
            similarity_scores.sort(key=lambda x: x['weighted_score'], reverse=True)
            
            # 保存结果
            result_dir = output_dir / "results" / arxiv_id
            result_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制原图
            import shutil
            final_original = result_dir / "original.png"
            shutil.copy2(flowchart_path, final_original)
            
            # 按排名复制生成的图片（排名第一的为generated_1.png）
            for rank, item in enumerate(similarity_scores, 1):
                final_gen = result_dir / f"generated_{rank}.png"
                shutil.copy2(item['path'], final_gen)
            
            # 保存prompt到文件（按排名顺序）
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
            
            results.append({
                'paper': paper,
                'arxiv_id': arxiv_id,
                'original_image': final_original,
                'prompts': [item['prompt'] for item in similarity_scores],
                'generated_images': [result_dir / f"generated_{i+1}.png" for i in range(len(generated_paths))],
                'similarity_scores': similarity_scores
            })
            
            images_collected += 1
            logger.info(f"✓ 成功处理第 {images_collected}/{args.num_images} 张流程图 "
                      f"(最佳相似度: {similarity_scores[0]['weighted_score']:.3f})")
            
            # 保存进度
            with open(progress_file, 'a') as f:
                f.write(f"{arxiv_id}\n")
        else:
            logger.warning(f"  所有图片生成失败，跳过")
    
    # 生成总结报告和精选结果
    logger.info("\n" + "="*80)
    logger.info("步骤4: 生成总结报告和精选结果")
    logger.info("="*80)
    
    # 创建精选结果文件夹（只包含原图、排名第一的生图及其prompt）
    curated_dir = output_dir / "curated_results"
    curated_dir.mkdir(parents=True, exist_ok=True)
    
    for result in results:
        arxiv_id = result['arxiv_id']
        if result.get('similarity_scores') and len(result['similarity_scores']) > 0:
            # 排名第一的结果
            best_result = result['similarity_scores'][0]
            
            # 创建该论文的精选文件夹
            paper_curated_dir = curated_dir / arxiv_id
            paper_curated_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制原图
            import shutil
            shutil.copy2(result['original_image'], paper_curated_dir / "original.png")
            
            # 复制排名第一的生成图
            best_image_path = result['generated_images'][0]  # 已经是按排名排序的
            shutil.copy2(best_image_path, paper_curated_dir / "generated_best.png")
            
            # 保存排名第一的prompt
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
            
            logger.info(f"✓ 已创建精选结果: {arxiv_id} (得分: {best_result['weighted_score']:.3f})")
    
    summary_file = output_dir / "summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("图片Prompt测试总结报告\n")
        f.write("="*80 + "\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"目标图片数: {args.num_images}\n")
        f.write(f"实际收集图片数: {len(results)}\n")
        f.write(f"处理论文数: {papers_processed}\n")
        f.write(f"每个原图生成prompt数: {args.num_prompts}\n\n")
        f.write("="*80 + "\n\n")
        
        # 统计平均相似度
        if results:
            avg_scores = []
            for result in results:
                if result.get('similarity_scores') and len(result['similarity_scores']) > 0:
                    avg_scores.append(result['similarity_scores'][0]['weighted_score'])
            
            if avg_scores:
                f.write(f"平均最佳相似度得分: {sum(avg_scores) / len(avg_scores):.4f}\n")
                f.write(f"最高相似度得分: {max(avg_scores):.4f}\n")
                f.write(f"最低相似度得分: {min(avg_scores):.4f}\n\n")
        
        f.write("="*80 + "\n")
        f.write("详细结果:\n")
        f.write("="*80 + "\n\n")
        
        for i, result in enumerate(results, 1):
            f.write(f"\n图片 {i}:\n")
            f.write(f"  论文: {result['paper']['title']}\n")
            f.write(f"  arXiv ID: {result['arxiv_id']}\n")
            f.write(f"  原图: {result['original_image']}\n")
            f.write(f"  生成图片数: {len(result['generated_images'])}\n")
            if result.get('similarity_scores') and len(result['similarity_scores']) > 0:
                best = result['similarity_scores'][0]
                f.write(f"  最佳相似度得分: {best['weighted_score']:.4f}\n")
                f.write(f"     - SSIM: {best['scores']['ssim']:.4f}\n")
                f.write(f"     - 特征匹配: {best['scores']['feature_match']:.4f}\n")
                f.write(f"     - 深度学习: {best['scores']['deep_learning']:.4f}\n")
            f.write(f"  详情目录: results/{result['arxiv_id']}/\n")
            f.write("-"*80 + "\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("精选结果已保存在: curated_results/ 目录\n")
        f.write("每个论文文件夹包含: original.png, generated_best.png, best_prompt.txt\n")
    
    logger.info("="*80)
    logger.info(f"完成！")
    logger.info(f"  收集了 {len(results)} 张流程图")
    logger.info(f"  处理了 {papers_processed} 篇论文")
    logger.info(f"  输出目录: {output_dir}")
    logger.info(f"  每个结果保存在: {output_dir}/results/<arxiv_id>/")
    logger.info(f"  精选结果保存在: {output_dir}/curated_results/<arxiv_id>/")
    logger.info("="*80)


if __name__ == '__main__':
    main()
