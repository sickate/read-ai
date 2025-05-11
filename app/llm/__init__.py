"""
LLM 模块初始化文件
提供大语言模型接口和工具函数
"""

# Usage: python -m utils.llm_v2 --provider aliyun --model qwen-max --prompt "who are you?"

from .providers import (
    get_provider_config,
    validate_model,
    SiliconFlowProvider,
    AliyunProvider,
    XAIProvider,
    GeminiProvider,
    OpenAIProvider,
    PROVIDER_MAP
)

__all__ = [
    'get_provider_config',
    'validate_model',
    'SiliconFlowModel',
    'AliyunModel',
    'XAIModel',
    'GeminiModel',
    'OpenAIModel',
    'get_default_llm',
    'generate_text'
]

# 默认使用阿里云提供者 (注意：provider 名称应该是小写的)
default_llm = get_provider_config('aliyun').get_llm()

def get_default_llm():
    """获取默认的 LLM 客户端"""
    return default_llm

async def generate_text(prompt, provider='aliyun', model=None):
    """生成文本的简单接口
    
    Args:
        prompt: 提示文本
        provider: 提供者名称，默认为 'aliyun'
        model: 模型名称，如果为 None 则使用提供者的默认模型
        
    Returns:
        str: 生成的文本
    """
    provider_instance = get_provider_config(provider.lower())
    llm = provider_instance.get_llm()
    
    # 构建请求参数
    params = {
        "model": model or provider_instance.__default_model__,
        "messages": [{"role": "user", "content": prompt}],
        # "stream": True,
    }
    
    # 发送请求
    response = llm.chat.completions.create(**params)
    return response.choices[0].message.content