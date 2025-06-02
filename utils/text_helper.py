import re
from typing import Dict, Any


def analyze_text(text: str) -> Dict[str, Any]:
    """
    分析文本，统计汉字字数、标点符号数和英文单词数
    
    Args:
        text (str): 要分析的文本
        
    Returns:
        Dict[str, Any]: 包含统计结果的字典
            - chinese_chars: 汉字字数
            - punctuation: 标点符号数（包括全角和半角）
            - english_words: 英文单词数
            - total_chars: 总字符数
    """
    if not text:
        return {
            "chinese_chars": 0,
            "punctuation": 0,
            "english_words": 0,
            "total_chars": 0
        }
    
    # 统计汉字 (使用常用汉字的Unicode范围)
    # \u4e00-\u9fff: CJK统一汉字基本区域
    chinese_pattern = r'[\u4e00-\u9fff]'
    chinese_chars = len(re.findall(chinese_pattern, text))
    
    # 统计标点符号 (包括中文和英文标点)
    # 中文标点符号和全角符号
    chinese_punctuation_pattern = r'[\u3000-\u303f\uff00-\uffef]'
    # 英文标点符号
    english_punctuation_pattern = r'[!\"#$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~]'
    
    # 分别统计中英文标点
    chinese_punctuation_count = len(re.findall(chinese_punctuation_pattern, text))
    english_punctuation_count = len(re.findall(english_punctuation_pattern, text))
    punctuation = chinese_punctuation_count + english_punctuation_count
    
    # 统计英文单词数
    # 匹配英文单词 (连续的字母，可能包含撇号)
    english_word_pattern = r"[a-zA-Z]+(?:'[a-zA-Z]+)?"
    english_words = len(re.findall(english_word_pattern, text))
    
    # 总字符数
    total_chars = len(text)
    
    return {
        "chinese_chars": chinese_chars,
        "punctuation": punctuation,
        "english_words": english_words,
        "total_chars": total_chars
    }


def format_analysis_result(result: Dict[str, Any]) -> str:
    """
    格式化分析结果为可读字符串
    
    Args:
        result (Dict[str, Any]): analyze_text函数的返回结果
        
    Returns:
        str: 格式化的结果字符串
    """
    return f"""
📊 文本分析结果:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 汉字字数:     {result['chinese_chars']:,}
🔤 英文单词数:   {result['english_words']:,}
🔣 标点符号数:   {result['punctuation']:,}
📄 总字符数:     {result['total_chars']:,}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


if __name__ == "__main__":
    # 测试函数
    test_text = "你好，世界！Hello, world! 这是一个测试文本。This is a test."
    result = analyze_text(test_text)
    print(format_analysis_result(result)) 