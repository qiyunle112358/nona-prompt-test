"""
通用LLM客户端
使用requests直接调用API，支持任何兼容OpenAI格式的服务
"""

import requests
import json
import logging
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


def call_llm(
    base_url: str,
    api_key: str,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
    response_format: Optional[Dict] = None,
    timeout: int = 120
) -> Optional[Dict]:
    """
    调用LLM API（兼容OpenAI格式）
    
    Args:
        base_url: API基础URL（如 https://api.openai.com/v1 或 https://openrouter.ai/api/v1）
        api_key: API密钥
        model: 模型名称
        messages: 消息列表
        temperature: 温度参数（0-1）
        max_tokens: 最大token数
        response_format: 响应格式，如 {"type": "json_object"}
        timeout: 超时时间（秒）
        
    Returns:
        响应内容字典，包含 'content' 和 'usage' 字段
        返回 None 表示调用失败
    """
    
    # 确保 base_url 以正确的端点结尾
    if not base_url.endswith('/chat/completions'):
        if base_url.endswith('/'):
            url = f"{base_url}chat/completions"
        else:
            url = f"{base_url}/chat/completions"
    else:
        url = base_url
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }
    
    if max_tokens:
        payload["max_tokens"] = max_tokens
    
    if response_format:
        payload["response_format"] = response_format
    
    try:
        logger.debug(f"Calling LLM API: {url} with model: {model}")
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()
        
        # 解析响应
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}")
            logger.error(f"Raw response: {response.text[:500]}")
            return None
        
        # 提取内容
        if not response_data.get('choices'):
            logger.error(f"No choices in response: {response_data}")
            return None
        
        message = response_data['choices'][0]['message']
        content = message.get('content', '')
        usage = response_data.get('usage', {})
        
        return {
            'content': content,
            'usage': usage
        }
        
    except requests.exceptions.Timeout:
        logger.error(f"Request timeout after {timeout}s")
        return None
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                logger.error(f"API error detail: {error_detail}")
            except:
                logger.error(f"API error response: {e.response.text[:500]}")
        return None
    
    except (KeyError, IndexError) as e:
        logger.error(f"Error parsing response structure: {e}")
        logger.error(f"Response data: {response_data}")
        return None
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None


def test_connection(
    base_url: str,
    api_key: str,
    model: str
) -> bool:
    """
    测试LLM API连接是否正常
    
    Args:
        base_url: API基础URL
        api_key: API密钥
        model: 模型名称
        
    Returns:
        True表示连接成功，False表示失败
    """
    
    messages = [
        {"role": "user", "content": "请用一句话介绍你自己"}
    ]
    
    result = call_llm(
        base_url=base_url,
        api_key=api_key,
        model=model,
        messages=messages,
        max_tokens=100,
        timeout=30
    )
    
    return result is not None and result.get('content')

