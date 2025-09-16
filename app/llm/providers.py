"""Configuration for LLM providers and models.

This module contains configuration settings for supported LLM providers,
including model types and API keys.
"""

import os
from typing import List, Dict, Any
from enum import Enum, auto
from dotenv import load_dotenv
from openai import OpenAI
# from llama_index.llms.openai import OpenAI as OpenAILLM
# from llama_index.llms.openai_like import OpenAILike
import requests
import dashscope
from dashscope.audio.asr import Recognition

from http import HTTPStatus
from dashscope.audio.asr import Transcription
import json


# Load environment variables
load_dotenv()

# 模型枚举类
class SiliconFlowModel(str, Enum):
    """SiliconFlow模型枚举"""
    DEEPSEEK_V3 = "deepseek-ai/DeepSeek-V3"
    DEEPSEEK_R1 = "deepseek-ai/DeepSeek-R1"
    DEEPSEEK_V3_PRO = "Pro/deepseek-ai/DeepSeek-V3"
    DEEPSEEK_R1_PRO = "Pro/deepseek-ai/DeepSeek-R1"
    QWEN2_5_72B_INSTRUCT = "Qwen/Qwen2.5-72B-Instruct"
    QWEN2_5_7B_INSTRUCT = "Qwen/Qwen2.5-7B-Instruct" # Free

class AliyunModel(str, Enum):
    """阿里云模型枚举"""
    DEEPSEEK_R1 = 'deepseek-r1'
    DEEPSEEK_V3 = 'deepseek-v3'
    QWEN_MAX_LATEST = 'qwen-max-latest'
    QWEN_MAX = 'qwen-max'
    QWEN_OMNI_TURBO = 'qwen-omni-turbo-latest'
    QWEN_OMNI_TURBO_2025_01_19 = 'qwen-omni-turbo-2025-01-19'
    QWEN_MAX_2025_01_25 = 'qwen-max-2025-01-25'
    QWEN_PLUS = 'qwen-plus'
    QWEN_PLUS_LATEST = 'qwen-plus-latest'
    QWEN_PLUS_2025_01_25 = 'qwen-plus-2025-01-25'
    QWQ_PLUS = 'qwq-plus'
    QWEN_TURBO = 'qwen-turbo'
    QWEN2_5_VL_72B_INSTRUCT = 'qwen2.5-vl-72b-instruct'
    FLUX_SCHNELL = 'flux-schnell'
    QWEN2_5_14B_INSTRUCT_1M = 'qwen2.5-14b-instruct-1m'
    PARAFORMER_V1 = 'paraformer-v1'
    PARAFORMER_V2 = 'paraformer-v2'


class XAIModel(str, Enum):
    """XAI模型枚举"""
    GROK_2_VISION = 'grok-2-vision-1212'
    GROK_2 = 'grok-2-1212'


class GeminiModel(str, Enum):
    """Gemini模型枚举"""
    GEMINI_2_5_PRO_EXP = "gemini-2.5-pro-exp-03-25"
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite" # Ultra lightweight model for basic tasks
    GEMINI_2_0_FLASH = "gemini-2.0-flash" # in/out price per million: USD $0.1/$0.4
    GEMINI_2_0_FLASH_LITE = "gemini-2.0-flash-lite" # in/out price per million: USD $0.075/$0.3
    GEMINI_1_5_PRO = "gemini-1.5-pro"
    GEMINI_1_5_FLASH_8B = "gemini-1.5-flash-8b" # Cheap and fast
    GEMINI_EMBEDDING_EXP = "gemini-embedding-exp"
    IMAGEN_3_0_GENERATE = "imagen-3.0-generate-002" # per image: USD $0.03
    GEMMA_3_27B = 'gemma-3-27b-it'

class OpenAIModel(str, Enum):
    """OpenAI模型枚举"""
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_O1 = "gpt-o1"
    GPT_O3_MINI = "gpt-o3-mini"

class VolcanoArkModel(str, Enum):
    """VolcanoArk模型枚举"""
    DEEPSEEK_R1 = 'deepseek-r1-250120'
    DEEPSEEK_R1_DISTILL_QWEN_32B = 'deepseek-r1-distill-qwen-32b-250120'
    DEEPSEEK_V3 = 'deepseek-v3-250120'


class ProviderBase:
    """基础提供者类，所有LLM提供者都应继承此类"""

    __provider__: str
    __api_base__: str
    __api_key__: str
    __models__: List[str]
    __default_model__: str
    __cheap_model__: str
    __special_args__: Dict[str, Any] = {}  # some provider has special args

    def get_llm(self, **kwargs):
        """获取OpenAI兼容的LLM客户端

        Args:
            **kwargs: 传递给OpenAI客户端的额外参数

        Returns:
            OpenAI: OpenAI客户端实例
        """
        # get openai compatible llm
        if self.__provider__ == 'openai':
            return OpenAI(
                api_key=self.__api_key__,
                **kwargs
            )
        else:
            return OpenAI(
                api_key=self.__api_key__,
                base_url=self.__api_base__,
                **kwargs
            )

    # def get_llm_llama_index(self, model=None, **kwargs):
    #     """获取Llama Index兼容的LLM客户端
    #
    #     Args:
    #         model: 要使用的模型名称，如果为None则使用默认模型
    #         **kwargs: 传递给LlamaIndex客户端的额外参数
    #
    #     Returns:
    #         Union[OpenAILLM, OpenAILike]: LlamaIndex兼容的LLM客户端
    #     """
    #     # get llama_index compatible llm
    #     model = model or self.__default_model__
    #     if self.__provider__ == 'openai':
    #         return OpenAILLM(
    #             model=model,
    #             api_key=self.__api_key__,
    #             **kwargs
    #         )
    #     else:
    #         return OpenAILike(
    #             model=model,
    #             api_key=self.__api_key__,
    #             api_base=self.__api_base__,
    #             is_chat_model=True,
    #             **kwargs 
    #         )


class SiliconFlowProvider(ProviderBase):
    """SiliconFlow提供者配置"""

    __provider__ = "siliconflow"
    __api_base__ = "https://api.siliconflow.cn/v1"
    __api_key__ = os.getenv("SILICON_FLOW_API_KEY")
    __default_model__ = SiliconFlowModel.DEEPSEEK_V3.value
    __cheap_model__ = SiliconFlowModel.DEEPSEEK_V3.value
    __models__ = [model.value for model in SiliconFlowModel]

class AliyunProvider(ProviderBase):
    """阿里云提供者配置"""

    __provider__ = "aliyun"
    __api_base__ = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    __api_key__ = os.getenv("DASHSCOPE_API_KEY")
    __default_model__ = AliyunModel.QWEN_MAX.value
    __cheap_model__ = AliyunModel.QWEN_PLUS_LATEST.value
    __models__ = [model.value for model in AliyunModel]


class XAIProvider(ProviderBase):
    """XAI提供者配置"""

    __provider__ = "xai"
    __api_base__ = "https://api.xai.com/v1"
    __api_key__ = os.getenv("XAI_API_KEY")
    __default_model__ = XAIModel.GROK_2.value
    __cheap_model__ = XAIModel.GROK_2.value
    __models__ = [model.value for model in XAIModel]

class GeminiProvider(ProviderBase):
    """Gemini提供者配置"""

    __provider__ = "gemini"
    __api_base__ = "https://generativelanguage.googleapis.com/v1beta/openai/"
    __api_key__ = os.getenv("GOOGLE_API_KEY")
    __default_model__ = GeminiModel.GEMINI_1_5_PRO.value
    __cheap_model__ = GeminiModel.GEMINI_2_0_FLASH.value
    __models__ = [model.value for model in GeminiModel]

class VolcanoArkProvider(ProviderBase):
    """VolcanoArk提供者配置"""

    __provider__ = "volcano"
    __api_base__ = "https://ark.cn-beijing.volces.com/api/v3/"
    __api_key__ = os.getenv("VOLCANOARK_API_KEY")
    __appid__ = os.getenv("VOLCANOARK_APPID")
    __default_model__ = VolcanoArkModel.DEEPSEEK_R1.value
    __models__ = [model.value for model in VolcanoArkModel]

class OpenAIProvider(ProviderBase):
    """OpenAI提供者配置"""

    __provider__ = "openai"
    __api_key__ = os.getenv("OPENAI_API_KEY")
    __default_model__ = OpenAIModel.GPT_4O.value
    __cheap_model__ = OpenAIModel.GPT_4O_MINI.value
    __models__ = [model.value for model in OpenAIModel]

# 提供者映射表，用于根据名称获取提供者类
PROVIDER_MAP = {
    'openai': OpenAIProvider,
    'aliyun': AliyunProvider,
    'xai': XAIProvider,
    'siliconflow': SiliconFlowProvider,
    'gemini': GeminiProvider,
    'volcano': VolcanoArkProvider,
}


def get_provider_config(provider: str) -> ProviderBase:
    """获取特定提供者的配置实例
    
    Args:
        provider: 提供者名称
        
    Returns:
        ProviderBase: 提供者配置实例
        
    Raises:
        ValueError: 如果提供者不受支持
    """
    if provider not in PROVIDER_MAP:
        raise ValueError(f"不支持的提供者: {provider}")
    return PROVIDER_MAP[provider]()


def validate_model(provider: str, model: str) -> bool:
    """验证模型是否被提供者支持
    
    Args:
        provider: 提供者名称
        model: 模型名称
        
    Returns:
        bool: 如果模型受支持则为True，否则为False
    """
    provider_instance = get_provider_config(provider)
    return model in provider_instance.__models__

def generate_subtitle_with_dashscope(audio_path: str, api_key: str = None) -> str:
    """
    使用 dashscope SDK 的 paraformer-v2 模型生成音频字幕（SRT 格式）
    
    Args:
        audio_path: 本地音频文件路径
        api_key: dashscope API key（可选，默认读取环境变量）
    
    Returns:
        SRT 字幕内容字符串
    
    Raises:
        Exception: 生成失败时抛出
    """
    api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
    dashscope.api_key = api_key

    is_url = audio_path.startswith('http')

    # 定义回调类，用于接收识别结果
    class ResultCallback:
        def __init__(self):
            self.sentences = []
            self.current_index = 1
            self.debug_info = []
            
        def on_sentence_begin(self, result):
            self.debug_info.append(f"on_sentence_begin: {str(result)}")
            
        def on_sentence_end(self, result):
            self.debug_info.append(f"on_sentence_end: {str(result)}")
            try:
                # 查看 result 是否有 sentences 属性或键
                if hasattr(result, 'sentences'):
                    sentences = result.sentences
                elif isinstance(result, dict) and 'sentences' in result:
                    sentences = result['sentences']
                else:
                    # 尝试解析整个文本并给定一个估计的时间范围
                    if hasattr(result, 'text') and result.text:
                        text = result.text
                    elif isinstance(result, dict) and 'text' in result:
                        text = result['text']
                    else:
                        return
                        
                    if text and text.strip():
                        # 为整段文本创建一个简单的字幕
                        begin_time = "00:00:00,000"
                        end_time = "00:01:00,000" # 假设 1 分钟
                        self.sentences.append(f"{self.current_index}\n{begin_time} --> {end_time}\n{text.strip()}\n")
                        self.current_index += 1
                    return
                
                # 处理句子列表
                for sentence in sentences:
                    if isinstance(sentence, dict):
                        if 'text' in sentence and sentence['text'].strip():
                            # 尝试获取时间信息
                            begin_time = self._get_time(sentence, 'begin_time', 0)
                            end_time = self._get_time(sentence, 'end_time', 10000)
                            text = sentence['text'].strip()
                            
                            # 添加 SRT 格式字幕条目
                            self.sentences.append(f"{self.current_index}\n{begin_time} --> {end_time}\n{text}\n")
                            self.current_index += 1
            except Exception as e:
                self.debug_info.append(f"Error in on_sentence_end: {str(e)}")
                
        def on_completed(self, result):
            self.debug_info.append(f"on_completed: {str(result)}")
            # 如果没有解析到句子，尝试从最终结果中解析
            if not self.sentences and hasattr(result, 'text') and result.text:
                text = result.text
                if text and text.strip():
                    begin_time = "00:00:00,000"
                    end_time = "00:01:00,000"
                    self.sentences.append(f"{self.current_index}\n{begin_time} --> {end_time}\n{text.strip()}\n")
            
        def on_error(self, result):
            self.debug_info.append(f"on_error: {str(result)}")
            raise Exception(f"Recognition error: {result}")
            
        def on_start(self, result):
            self.debug_info.append(f"on_start: {str(result)}")
            
        def _get_time(self, sentence, key, default_ms):
            """安全地获取时间，处理可能的错误"""
            try:
                if key in sentence:
                    return self._format_time(sentence[key])
                else:
                    return self._format_time(default_ms)
            except:
                return self._format_time(default_ms)
            
        def _format_time(self, ms):
            """将毫秒转换为 SRT 格式的时间 (00:00:00,000)"""
            try:
                if isinstance(ms, str):
                    ms = float(ms)
                total_seconds = int(ms / 1000)
                ms = int(ms % 1000)
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"
            except:
                return "00:00:00,000"
            
        def get_srt(self):
            """获取完整的 SRT 字幕内容"""
            if not self.sentences:
                # 如果没有句子被解析，添加调试信息作为注释
                debug_str = "\n".join([f"# {line}" for line in self.debug_info])
                return f"1\n00:00:00,000 --> 00:00:10,000\n[未能识别有效内容]\n\n# Debug Info:\n{debug_str}"
            
            return "\n".join(self.sentences)
    
    # 创建回调对象
    callback = ResultCallback()
    
    try:
        # 创建识别器对象
        recognizer = Recognition(
            model='paraformer-v2',  # 使用官方示例中的格式
            format='mp3', 
            sample_rate=16000,  # 采样率
            callback=callback
        )
        
        # 打印一些基本信息
        print(f"Processing audio {'URL' if is_url else 'file'}: {audio_path}")
        
        # 根据输入类型调用不同的API
        if is_url:
            # 处理URL文件
            result = recognizer.call(file=audio_path)
        else:
            # 处理本地文件
            result = recognizer.call(file=audio_path)
            
        print(f"Recognition completed with result: {result}")
        
        # 返回 SRT 格式字幕
        return callback.get_srt()
    except Exception as e:
        print(f"Error in generate_subtitle_with_dashscope: {str(e)}")
        raise Exception(f"Error generating subtitle: {str(e)}")

def sample_call():
    # 若没有将API Key配置到环境变量中，需将下面这行代码注释放开，并将apiKey替换为自己的API Key
    # import dashscope
    # dashscope.api_key = "apiKey"

    task_response = Transcription.async_call(
        model='paraformer-v2',
        file_urls=['https://read-ai.instap.net/static/audios/ET3/disc1/04%20%E6%9B%B2%E7%9B%AE%204.mp3'],
        language_hints=['en'],  # "language_hints"只支持paraformer-v2模型
        api_key=os.getenv("DASHSCOPE_API_KEY")
    )

    transcribe_response = Transcription.wait(task=task_response.output.task_id)
    if transcribe_response.status_code == HTTPStatus.OK:
        print(json.dumps(transcribe_response.output, indent=4, ensure_ascii=False))


if __name__ == '__main__':
    sample_call()
