"""Text-to-Speech helper using Alibaba Cloud Qwen-TTS API.

This module provides text-to-speech functionality using Alibaba Cloud's
Qwen-TTS API, supporting multiple languages and voices.
"""

import os
import dashscope
from typing import Optional, Dict, Any
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TTSVoice:
    """Available TTS voices for Qwen3-TTS-Flash model"""
    # 通用音色 - 支持多语言
    CHERRY = "Cherry"  # 芊悦 - 亲切自然（女声）
    ETHAN = "Ethan"  # 晨煦 - 标准普通话（男声，北方口音）
    NOFISH = "Nofish"  # 不吃鱼 - 设计师风格（无卷舌音）
    JENNIFER = "Jennifer"  # 詹妮弗 - 品牌级电影质感（女声）
    RYAN = "Ryan"  # 甜茶 - 戏剧性高能量（男声）
    KATERINA = "Katerina"  # 卡捷琳娜 - 成熟有韵律（女声）
    ELIAS = "Elias"  # 墨讲师 - 学术叙事风格（男声）

    # 方言音色 - 主要中文
    JADA = "Jada"  # 上海-阿珍 - 上海话
    DYLAN = "Dylan"  # 北京-晓东 - 北京胡同风
    SUNNY = "Sunny"  # 四川-晴儿 - 四川话
    LI = "Li"  # 南京-老李 - 南京话
    MARCUS = "Marcus"  # 陕西-秦川 - 陕西话
    ROY = "Roy"  # 闽南-阿杰 - 闽南话（台湾风）
    PETER = "Peter"  # 天津-李彼得 - 天津话

    # 粤语音色
    ROCKY = "Rocky"  # 粤语-阿强 - 幽默粤语
    KIKI = "Kiki"  # 粤语-阿清 - 香港风粤语
    ERIC = "Eric"  # 四川-程川 - 成都话


class TTSLanguage:
    """Supported languages for TTS"""
    AUTO = "Auto"  # 自动检测
    CHINESE = "Chinese"  # 中文
    ENGLISH = "English"  # 英文
    JAPANESE = "Japanese"  # 日语
    KOREAN = "Korean"  # 韩语
    SPANISH = "Spanish"  # 西班牙语
    FRENCH = "French"  # 法语
    GERMAN = "German"  # 德语
    ITALIAN = "Italian"  # 意大利语
    PORTUGUESE = "Portuguese"  # 葡萄牙语
    RUSSIAN = "Russian"  # 俄语


def text_to_speech(
    text: str,
    voice: str = TTSVoice.CHERRY,
    language: str = TTSLanguage.AUTO,
    stream: bool = False,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert text to speech using Qwen-TTS API.

    Args:
        text: Text content to convert to speech
        voice: Voice ID to use (default: Cherry)
        language: Language type (default: Auto)
        stream: Whether to use streaming mode (default: False)
        api_key: DashScope API key (optional, reads from env if not provided)

    Returns:
        Dict containing:
            - success: bool
            - audio_url: str (if success and not stream)
            - audio_data: bytes (if success and stream)
            - error: str (if not success)

    Raises:
        ValueError: If text is empty or API key is missing
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    # Set API key
    api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY not found in environment variables")

    dashscope.api_key = api_key

    try:
        # Call Qwen-TTS API
        response = dashscope.MultiModalConversation.call(
            model="qwen3-tts-flash",
            api_key=api_key,
            text=text,
            voice=voice,
            language_type=language,
            stream=stream
        )

        # Check response status
        if response.status_code != 200:
            error_message = response.message if hasattr(response, 'message') else 'Unknown error'
            return {
                "success": False,
                "error": f"API request failed with status {response.status_code}: {error_message}"
            }

        # Process response based on stream mode
        if stream:
            # Streaming mode - collect audio chunks
            audio_chunks = []
            for chunk in response.output:
                if hasattr(chunk, 'audio') and chunk.audio:
                    audio_chunks.append(chunk.audio)

            if not audio_chunks:
                return {
                    "success": False,
                    "error": "No audio data received from API"
                }

            # Combine all chunks
            audio_data = b''.join(audio_chunks)

            return {
                "success": True,
                "audio_data": audio_data,
                "format": "wav"
            }
        else:
            # Non-streaming mode - get audio URL
            # According to docs, audio URL is at response.output.audio.url
            if not hasattr(response.output, 'audio') or not hasattr(response.output.audio, 'url'):
                return {
                    "success": False,
                    "error": "No audio URL in API response"
                }

            audio_url = response.output.audio.url

            return {
                "success": True,
                "audio_url": audio_url,
                "format": "wav"
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"TTS API error: {str(e)}"
        }


def get_available_voices() -> Dict[str, str]:
    """
    Get a dictionary of available voices with descriptions.

    Returns:
        Dict mapping voice ID to description
    """
    return {
        # 通用音色
        TTSVoice.CHERRY: "Cherry - 芊悦（亲切自然女声）",
        TTSVoice.ETHAN: "Ethan - 晨煦（标准普通话男声）",
        TTSVoice.NOFISH: "Nofish - 不吃鱼（设计师风格）",
        TTSVoice.JENNIFER: "Jennifer - 詹妮弗（电影质感女声）",
        TTSVoice.RYAN: "Ryan - 甜茶（高能量男声）",
        TTSVoice.KATERINA: "Katerina - 卡捷琳娜（成熟女声）",
        TTSVoice.ELIAS: "Elias - 墨讲师（学术风男声）",
        # 方言音色
        TTSVoice.DYLAN: "Dylan - 北京晓东（北京话）",
        TTSVoice.SUNNY: "Sunny - 四川晴儿（四川话）",
        TTSVoice.JADA: "Jada - 上海阿珍（上海话）",
        TTSVoice.ROCKY: "Rocky - 粤语阿强（粤语）",
        TTSVoice.KIKI: "Kiki - 粤语阿清（香港粤语）",
    }


def get_available_languages() -> Dict[str, str]:
    """
    Get a dictionary of available languages.

    Returns:
        Dict mapping language code to display name
    """
    return {
        TTSLanguage.AUTO: "自动检测",
        TTSLanguage.CHINESE: "中文",
        TTSLanguage.ENGLISH: "English",
        TTSLanguage.JAPANESE: "日本語",
        TTSLanguage.KOREAN: "한국어",
        TTSLanguage.SPANISH: "Español",
        TTSLanguage.FRENCH: "Français",
        TTSLanguage.GERMAN: "Deutsch",
    }


if __name__ == "__main__":
    # Test the TTS function
    test_text = "Hello, this is a test of text to speech functionality. 你好，这是文本转语音测试。"
    result = text_to_speech(test_text, voice=TTSVoice.CHERRY, language=TTSLanguage.AUTO)

    if result["success"]:
        print(f"TTS Success! Audio URL: {result.get('audio_url')}")
    else:
        print(f"TTS Failed: {result.get('error')}")
