"""
论文相关性分析器
使用LLM判断论文是否与指定主题相关，并生成总结
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional
from tqdm import tqdm

logger = logging.getLogger(__name__)


def analyze_paper(
    paper_text: str,
    paper_info: Dict,
    provider: str = "openai",
    relevance_tags: List[str] = None
) -> Optional[Dict]:
    """
    分析论文相关性
    
    Args:
        paper_text: 论文文本内容
        paper_info: 论文基本信息（标题、作者等）
        provider: LLM提供商 ("openai" 或 "anthropic")
        relevance_tags: 相关性标签列表
        
    Returns:
        分析结果字典: {
            'is_relevant': bool,
            'relevance_score': float,
            'reasoning': str,
            'summary': str
        }
    """
    try:
        logger.info(f"Analyzing paper: {paper_info.get('title', 'Unknown')}")
        
        # 如果没有提供标签，使用默认标签
        if relevance_tags is None:
            from config import RELEVANCE_TAGS
            relevance_tags = RELEVANCE_TAGS
        
        # 构建提示词
        prompt = _build_analysis_prompt(paper_text, paper_info, relevance_tags)
        
        # 调用LLM
        if provider == "openai":
            result = _call_openai(prompt)
        elif provider == "anthropic":
            result = _call_anthropic(prompt)
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        if result:
            logger.info(f"✓ Analysis complete. Relevant: {result.get('is_relevant')}, Score: {result.get('relevance_score')}")
            return result
        else:
            logger.error("Failed to analyze paper")
            return None
            
    except Exception as e:
        logger.error(f"Error analyzing paper: {e}")
        return None


def batch_analyze_papers(
    papers: List[Dict],
    text_dir: Path,
    provider: str = "openai",
    relevance_tags: List[str] = None,
    show_progress: bool = True
) -> List[Dict]:
    """
    批量分析论文
    
    Args:
        papers: 论文列表
        text_dir: 文本文件目录
        provider: LLM提供商
        relevance_tags: 相关性标签
        show_progress: 是否显示进度条
        
    Returns:
        分析结果列表
    """
    results = []
    
    iterator = tqdm(papers, desc="Analyzing papers") if show_progress else papers
    
    for paper in iterator:
        paper_id = paper.get('arxiv_id') or paper.get('id')
        
        if not paper_id:
            logger.warning(f"Missing paper ID for: {paper.get('title')}")
            continue
        
        # 读取文本文件
        text_path = text_dir / f"{paper_id}.txt"
        
        if not text_path.exists():
            logger.warning(f"Text file not found: {text_path}")
            continue
        
        try:
            with open(text_path, 'r', encoding='utf-8') as f:
                paper_text = f.read()
            
            # 限制文本长度（避免超过token限制）
            paper_text = _truncate_text(paper_text, max_chars=50000)
            
            # 分析论文
            result = analyze_paper(paper_text, paper, provider, relevance_tags)
            
            if result:
                # 添加paper_id到结果中
                result['paper_id'] = paper_id
                results.append(result)
                
        except Exception as e:
            logger.error(f"Error processing paper {paper_id}: {e}")
            continue
    
    logger.info(f"Successfully analyzed {len(results)}/{len(papers)} papers")
    return results


def _build_analysis_prompt(
    paper_text: str,
    paper_info: Dict,
    relevance_tags: List[str]
) -> str:
    """构建分析提示词"""
    
    tags_str = ", ".join(relevance_tags)
    
    prompt = f"""请分析以下论文，判断它是否与这些研究主题相关：{tags_str}

论文标题：{paper_info.get('title', 'Unknown')}

论文作者：{', '.join(paper_info.get('authors', [])[:5])}

论文摘要：
{paper_info.get('abstract', 'N/A')[:1000]}

论文内容（部分）：
{paper_text[:10000]}

请按照以下JSON格式返回分析结果：
{{
    "is_relevant": true/false,
    "relevance_score": 0.0-1.0,
    "reasoning": "判断理由（中文，2-3句话）",
    "summary": "论文总结（中文，包括：研究问题、方法、主要贡献、实验结果，200-300字）"
}}

评分标准：
- 1.0: 高度相关，核心研究内容直接关联
- 0.7-0.9: 相关性强，有显著关联
- 0.4-0.6: 中等相关，有一定关联
- 0.1-0.3: 弱相关，仅有少量关联
- 0.0: 不相关

请只返回JSON，不要有其他内容。
"""
    
    return prompt


def _call_openai(prompt: str) -> Optional[Dict]:
    """调用OpenAI API"""
    try:
        from config import get_api_key, get_model_name, OPENAI_BASE_URL
        import openai
        
        api_key = get_api_key("openai")
        model = get_model_name("openai")
        
        if not api_key:
            logger.error("OpenAI API key not configured")
            return None
        
        client = openai.OpenAI(api_key=api_key, base_url=OPENAI_BASE_URL)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个专业的科研论文分析助手，擅长判断论文的研究方向和相关性。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        return result
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return None


def _call_anthropic(prompt: str) -> Optional[Dict]:
    """调用Anthropic API"""
    try:
        from config import get_api_key, get_model_name
        import anthropic
        
        api_key = get_api_key("anthropic")
        model = get_model_name("anthropic")
        
        if not api_key:
            logger.error("Anthropic API key not configured")
            return None
        
        client = anthropic.Anthropic(api_key=api_key)
        
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            temperature=0.3,
            system="你是一个专业的科研论文分析助手，擅长判断论文的研究方向和相关性。请始终以JSON格式返回结果。",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        content = response.content[0].text
        
        # 尝试提取JSON
        json_match = content.strip()
        if json_match.startswith('```json'):
            json_match = json_match[7:]
        if json_match.endswith('```'):
            json_match = json_match[:-3]
        
        result = json.loads(json_match.strip())
        
        return result
        
    except Exception as e:
        logger.error(f"Error calling Anthropic API: {e}")
        return None


def _truncate_text(text: str, max_chars: int = 50000) -> str:
    """
    截断文本到指定长度
    保留开头和结尾部分
    """
    if len(text) <= max_chars:
        return text
    
    # 保留前80%和后20%
    head_chars = int(max_chars * 0.8)
    tail_chars = int(max_chars * 0.2)
    
    head = text[:head_chars]
    tail = text[-tail_chars:]
    
    return head + "\n\n[... 中间部分已省略 ...]\n\n" + tail

