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
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import requests
from PIL import Image
import fitz  # PyMuPDF

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_PATH, PDF_DIR, LOG_LEVEL, LOG_FORMAT
from database import Database
import collectors

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
    """OpenRouter API客户端"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
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
            
            # 构建prompt，要求生成非常详细的prompt
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
            response = requests.post(url, headers=self.headers, json=payload, timeout=120)
            
            if response.status_code != 200:
                logger.error(f"API请求失败: {response.status_code} - {response.text}")
                return []
            
            result = response.json()
            
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
            response = requests.post(url, headers=self.headers, json=payload, timeout=600)
            
            if response.status_code != 200:
                logger.error(f"API请求失败: {response.status_code} - {response.text}")
                return False
            
            result = response.json()
            
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
    
    # 关键词列表（中文及其英文对应）
    KEYWORDS = [
        # 中文关键词
        '流程图', '技术路线', '框架图', '实验设计', '工作流程', '架构图',
        # 对应的英文关键词
        'Flowchart', 'Technical Roadmap', 'Framework Diagram', 'Experimental Design', 
        'Workflow', 'Architecture Diagram', 'Architecture',
        # 其他相关英文关键词
        'Figure', 'System Architecture', 'Method Overview', 'Pipeline'
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
        
        # 中文关键词及其英文对应
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
                # 也搜索其他相关英文变体
                elif any(variant.lower() in text_lower for variant in [
                    'Architecture', 'Framework', 'Flow Chart', 'Work Flow',
                    'Experimental Design', 'Technical Roadmap'
                ]):
                    # 检查是否是相关的关键词
                    for variant in ['Architecture', 'Framework', 'Flow Chart', 'Work Flow', 
                                   'Experimental Design', 'Technical Roadmap']:
                        if variant.lower() in text_lower:
                            found = True
                            matched_keyword = variant
                            break
                
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
        提取关键词所在页面附近的图片
        
        Args:
            doc: PDF文档对象
            page_num: 页面编号
            keyword: 关键词
            
        Returns:
            提取的图片路径，如果没有找到返回None
        """
        try:
            page = doc[page_num]
            image_list = page.get_images()
            
            if not image_list:
                return None
            
            # 提取该页面的所有图片
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # 保存图片
                filename = f"diagram_page_{page_num}_img_{img_index}.{image_ext}"
                image_path = self.output_dir / filename
                
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)
                
                # 基本检查：排除太小的图片
                try:
                    img_pil = Image.open(image_path)
                    width, height = img_pil.size
                    if width >= 200 and height >= 200:  # 至少200x200像素
                        logger.info(f"提取图片: {filename} (关键词: {keyword}, 页面: {page_num+1})")
                        return image_path
                    else:
                        # 删除太小的图片
                        image_path.unlink()
                except Exception:
                    # 如果无法打开图片，也删除
                    if image_path.exists():
                        image_path.unlink()
            
            return None
            
        except Exception as e:
            logger.error(f"提取图片时出错 (页面{page_num+1}): {e}")
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
    parser = argparse.ArgumentParser(description='图片Prompt测试脚本 - 完整流程')
    parser.add_argument('--num-images', type=int, default=100, help='要收集的流程图数量（默认100）')
    parser.add_argument('--year', type=int, default=2024, help='论文年份（默认2024）')
    parser.add_argument('--openrouter-api-key', type=str, required=True, help='OpenRouter API密钥')
    parser.add_argument('--num-prompts', type=int, default=5, help='每个原图生成的prompt数量（默认5）')
    parser.add_argument('--output-dir', type=str, default='data/prompt_test', help='输出目录')
    parser.add_argument('--max-papers', type=int, default=500, help='最多处理的论文数量（默认500）')
    
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
    
    # 步骤1: 收集论文
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
    
    # 步骤3: 下载PDF并提取流程图
    logger.info("\n" + "="*80)
    logger.info("步骤3: 下载PDF并提取流程图")
    logger.info("="*80)
    
    to_download_papers = db.get_papers_by_status('TobeDownloaded', limit=args.max_papers)
    if not to_download_papers:
        logger.warning("没有待下载的论文")
        return
    
    results = []
    images_collected = 0
    papers_processed = 0
    
    for paper in to_download_papers:
        if images_collected >= args.num_images:
            break
        
        arxiv_id = paper.get('arxiv_id')
        pdf_url = paper.get('pdf_url')
        
        if not arxiv_id or not pdf_url:
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
        
        # 为每个prompt生成图片
        logger.info(f"  生成 {len(prompts)} 张图片...")
        generated_paths = []
        
        for i, prompt in enumerate(prompts, 1):
            gen_dir = output_dir / "generated_images" / arxiv_id
            gen_path = gen_dir / f"prompt_{i}.png"
            
            if api_client.text_to_image(prompt, gen_path):
                generated_paths.append(gen_path)
                logger.info(f"    ✓ Prompt {i} 图片已生成")
            else:
                logger.warning(f"    ✗ Prompt {i} 图片生成失败")
        
        if generated_paths:
            # 保存结果
            result_dir = output_dir / "results" / arxiv_id
            result_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制原图
            import shutil
            final_original = result_dir / "original.png"
            shutil.copy2(flowchart_path, final_original)
            
            # 复制生成的图片
            for i, gen_path in enumerate(generated_paths, 1):
                final_gen = result_dir / f"generated_{i}.png"
                shutil.copy2(gen_path, final_gen)
            
            # 保存prompt到文件
            prompts_file = result_dir / "prompts.txt"
            with open(prompts_file, 'w', encoding='utf-8') as f:
                f.write(f"论文: {paper['title']}\n")
                f.write(f"来源: {paper.get('source', 'N/A')}\n")
                f.write(f"arXiv ID: {arxiv_id}\n")
                f.write("="*80 + "\n\n")
                for i, prompt in enumerate(prompts, 1):
                    f.write(f"Prompt {i}:\n{prompt}\n\n")
                    f.write("-"*80 + "\n\n")
            
            results.append({
                'paper': paper,
                'arxiv_id': arxiv_id,
                'original_image': final_original,
                'prompts': prompts,
                'generated_images': [result_dir / f"generated_{i+1}.png" for i in range(len(generated_paths))]
            })
            
            images_collected += 1
            logger.info(f"✓ 成功处理第 {images_collected}/{args.num_images} 张流程图")
        else:
            logger.warning(f"  所有图片生成失败，跳过")
    
    # 生成总结报告
    logger.info("\n" + "="*80)
    logger.info("步骤4: 生成总结报告")
    logger.info("="*80)
    
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
        
        for i, result in enumerate(results, 1):
            f.write(f"\n图片 {i}:\n")
            f.write(f"  论文: {result['paper']['title']}\n")
            f.write(f"  arXiv ID: {result['arxiv_id']}\n")
            f.write(f"  原图: {result['original_image']}\n")
            f.write(f"  生成图片数: {len(result['generated_images'])}\n")
            f.write(f"  详情目录: results/{result['arxiv_id']}/\n")
            f.write("-"*80 + "\n")
    
    logger.info("="*80)
    logger.info(f"完成！")
    logger.info(f"  收集了 {len(results)} 张流程图")
    logger.info(f"  处理了 {papers_processed} 篇论文")
    logger.info(f"  输出目录: {output_dir}")
    logger.info(f"  每个结果保存在: {output_dir}/results/<arxiv_id>/")
    logger.info("="*80)


if __name__ == '__main__':
    main()
