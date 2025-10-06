"""
Gemini Vision API 文字识别模块
使用 Gemini 2.5 Flash 的多模态功能识别图片中的文字内容
"""
import os
import json
import base64
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class GeminiOCRProvider:
    """Gemini Vision OCR 服务提供者"""

    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY 环境变量未配置")

        # 使用转发服务的 API base URL
        self.api_base = "https://gemini.parallelstreamllc.com/v1beta"
        self.model = "gemini-2.5-flash"
        self.timeout = 60  # 60秒超时

    def recognize_image_from_file(self, image_path: str, language: str = 'auto') -> Dict[str, Any]:
        """
        从本地文件识别图片中的文字

        Args:
            image_path: 图片文件路径
            language: 语言类型 ('auto', 'zh', 'en', 'es')

        Returns:
            包含识别结果的字典
        """
        try:
            # 读取图片文件并编码为 base64
            with open(image_path, 'rb') as f:
                image_data = f.read()

            # 获取文件扩展名来确定 MIME 类型
            ext = os.path.splitext(image_path)[1].lower()
            mime_type = self._get_mime_type(ext)

            image_base64 = base64.b64encode(image_data).decode('utf-8')

            return self._recognize_image(image_base64, mime_type, language)

        except FileNotFoundError:
            return {
                "success": False,
                "error": f"文件未找到: {image_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"读取文件失败: {str(e)}"
            }

    def recognize_image_from_base64(self, image_base64: str, language: str = 'auto',
                                    mime_type: str = 'image/jpeg') -> Dict[str, Any]:
        """
        从 base64 编码的图片识别文字

        Args:
            image_base64: base64 编码的图片数据
            language: 语言类型 ('auto', 'zh', 'en', 'es')
            mime_type: 图片 MIME 类型

        Returns:
            包含识别结果的字典
        """
        return self._recognize_image(image_base64, mime_type, language)

    def _recognize_image(self, image_base64: str, mime_type: str, language: str) -> Dict[str, Any]:
        """
        调用 Gemini Vision API 识别图片中的文字

        Args:
            image_base64: base64 编码的图片数据
            mime_type: 图片 MIME 类型
            language: 语言类型

        Returns:
            包含识别结果的字典
        """
        try:
            # 构建提示词
            prompt = self._build_prompt(language)

            # 构建 Gemini API 请求
            url = f"{self.api_base}/models/{self.model}:generateContent"

            headers = {
                'x-goog-api-key': self.api_key,
                'Content-Type': 'application/json'
            }

            payload = {
                "contents": [{
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_base64
                            }
                        },
                        {"text": prompt}
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.1,  # 低温度以获得更准确的文字提取
                    "maxOutputTokens": 4096
                }
            }

            # 发送请求
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            # 检查响应状态
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Gemini API 请求失败: HTTP {response.status_code}"
                }

            # 解析响应
            return self._parse_gemini_response(response.json())

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Gemini API 请求超时，请稍后重试"
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"网络请求失败: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"OCR 识别失败: {str(e)}"
            }

    def _build_prompt(self, language: str) -> str:
        """
        根据语言构建 OCR 提示词

        Args:
            language: 语言类型

        Returns:
            提示词字符串
        """
        prompts = {
            'zh': """请识别这张图片中的所有中文文字内容。

这是一张作文照片，请准确提取所有文字，包括：
1. 保持原有的段落格式和换行
2. 忽略页边的涂鸦、折痕等干扰
3. 如果有手写字体，请尽可能准确识别
4. 保持标点符号的正确位置

只输出识别到的文字内容，不要添加任何说明或解释。""",

            'en': """Please extract all English text from this image.

This is an essay photo. Please accurately extract all text, including:
1. Maintain original paragraph formatting and line breaks
2. Ignore margin doodles, creases, and other interference
3. Recognize handwriting as accurately as possible
4. Keep punctuation in correct positions

Output only the recognized text content without any explanation.""",

            'es': """Por favor, extrae todo el texto en español de esta imagen.

Esta es una foto de ensayo. Extrae con precisión todo el texto, incluyendo:
1. Mantener el formato de párrafo original y saltos de línea
2. Ignorar garabatos en los márgenes, pliegues y otras interferencias
3. Reconocer la escritura a mano con la mayor precisión posible
4. Mantener la puntuación en posiciones correctas

Muestra solo el contenido de texto reconocido sin ninguna explicación.""",

            'auto': """Please extract all text from this image.

This is an essay or document photo. Please accurately extract all text:
1. Maintain original formatting and line breaks
2. Ignore margin notes, creases, and interference
3. Recognize both printed and handwritten text
4. Keep punctuation accurate

Output only the recognized text without any explanation."""
        }

        return prompts.get(language, prompts['auto'])

    def _parse_gemini_response(self, response: Dict) -> Dict[str, Any]:
        """
        解析 Gemini API 响应

        Args:
            response: API 响应字典

        Returns:
            格式化的识别结果
        """
        try:
            # 检查响应中是否有候选结果
            candidates = response.get('candidates', [])

            if not candidates:
                return {
                    "success": False,
                    "error": "Gemini API 未返回有效结果"
                }

            # 提取第一个候选结果
            candidate = candidates[0]
            content = candidate.get('content', {})
            parts = content.get('parts', [])

            if not parts:
                return {
                    "success": True,
                    "text": "",
                    "lines": [],
                    "message": "未识别到文字内容"
                }

            # 提取文字内容
            text_parts = []
            for part in parts:
                if 'text' in part:
                    text_parts.append(part['text'])

            full_text = '\n'.join(text_parts).strip()

            if not full_text:
                return {
                    "success": True,
                    "text": "",
                    "lines": [],
                    "message": "未识别到文字内容"
                }

            # 分割成行
            lines = [line.strip() for line in full_text.split('\n') if line.strip()]

            return {
                "success": True,
                "text": full_text,
                "lines": [{"text": line, "confidence": 1.0} for line in lines],
                "total_lines": len(lines)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"解析 Gemini 响应失败: {str(e)}"
            }

    def _get_mime_type(self, ext: str) -> str:
        """
        根据文件扩展名获取 MIME 类型

        Args:
            ext: 文件扩展名（包含点号）

        Returns:
            MIME 类型字符串
        """
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp'
        }
        return mime_types.get(ext.lower(), 'image/jpeg')


def recognize_text_from_image(image_path: Optional[str] = None,
                              image_base64: Optional[str] = None,
                              language: str = 'auto') -> Dict[str, Any]:
    """
    便捷函数：使用 Gemini Vision 识别图片中的文字

    Args:
        image_path: 图片文件路径（与 image_base64 二选一）
        image_base64: base64 编码的图片（与 image_path 二选一）
        language: 语言类型 ('auto', 'zh', 'en', 'es')

    Returns:
        包含识别结果的字典
        {
            "success": bool,
            "text": str,  # 完整文本
            "lines": List[Dict],  # 文本行列表
            "total_lines": int,  # 总行数
            "error": str  # 错误信息（如果失败）
        }
    """
    try:
        ocr_provider = GeminiOCRProvider()

        if image_base64:
            return ocr_provider.recognize_image_from_base64(image_base64, language)
        elif image_path:
            return ocr_provider.recognize_image_from_file(image_path, language)
        else:
            return {
                "success": False,
                "error": "必须提供 image_path 或 image_base64 参数"
            }

    except ValueError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"OCR 识别异常: {str(e)}"
        }


if __name__ == '__main__':
    # 测试代码
    test_image_path = 'test_image.jpg'
    if os.path.exists(test_image_path):
        print(f"测试识别图片: {test_image_path}")
        result = recognize_text_from_image(image_path=test_image_path, language='zh')
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"测试图片 {test_image_path} 不存在")
        print("请提供一张测试图片来验证 OCR 功能")
