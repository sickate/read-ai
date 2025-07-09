import re
from typing import Dict, Any, List
import os
import sys

# 添加项目根目录到路径，以便导入app模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.llm.providers import get_provider_config, AliyunModel


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


def ai_correct_essay(text: str, word_count: str = "不限字数", grade: str = "三年级") -> Dict[str, Any]:
    """
    使用AI批改作文，检查语法、错别字、标点符号等问题
    
    Args:
        text (str): 要批改的作文内容
        word_count (str): 作文字数要求
        grade (str): 年级
        
    Returns:
        Dict[str, Any]: 包含批改结果的字典
            - success: 是否成功
            - corrections: 修改建议列表
            - error: 错误信息（如果有）
    """
    if not text or not text.strip():
        return {
            "success": False,
            "error": "作文内容不能为空"
        }
    
    try:
        # 获取阿里云配置
        provider = get_provider_config('aliyun')
        client = provider.get_llm()
        
        # 构建批改提示词
        grade_requirements = {
            "一年级": "简单语句，基本表达清楚",
            "二年级": "句子通顺，有基本的段落概念",
            "三年级": "语句通顺，有开头、中间、结尾",
            "四年级": "结构清楚，语言较为流畅",
            "五年级": "内容充实，语言生动",
            "六年级": "文章结构完整，语言准确生动",
            "初一": "观点明确，论证有条理",
            "初二": "语言表达准确，有一定文采",
            "初三": "思想深刻，语言优美，结构严谨"
        }
        
        grade_req = grade_requirements.get(grade, "语句通顺，内容完整")
        word_count_req = f"字数要求：{word_count}" if word_count != "不限字数" else "字数无特殊要求"
        
        prompt = f"""请你作为一名专业的语文老师，仔细批改以下{grade}学生的作文。

【作文要求】
- 年级：{grade}
- {word_count_req}
- 评判标准：{grade_req}

【批改要求】
1. 不要修改原文，只标出需要修改的地方
2. 请按照以下格式输出，每个部分都要包含：

## 总体评价
- 总体印象：（对整篇作文的总体评价）
- 优点：（列出作文的优点）
- 主要问题：（列出主要需要改进的问题）
- 建议得分：（按{grade}标准给出建议分数，满分100分）

## 病句修改
- 第X段第Y句："原文内容" → 问题：具体问题描述 → 建议：如何修改的建议

## 错别字修改  
- 第X段："错字" → 应为："正字" → 位置：具体位置描述

## 标点符号修改
- 第X段：问题描述 → 建议：正确用法

## 语言表达改进建议
- 建议内容（给出建议和例子，但不直接提供修改后的原文）

## 内容结构改进建议
- 建议内容

【作文内容】
{text}

请开始批改："""

        # 调用AI模型
        response = client.chat.completions.create(
            model=AliyunModel.DEEPSEEK_R1.value,
            messages=[
                {"role": "system", "content": "你是一名专业的语文老师，负责批改学生作文。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        ai_response = response.choices[0].message.content
        
        # 解析AI返回的批改结果
        corrections = parse_correction_response(ai_response)
        
        return {
            "success": True,
            "corrections": corrections,
            "raw_response": ai_response
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"AI批改失败：{str(e)}"
        }


def ai_correct_essay_stream(text: str, word_count: str = "不限字数", grade: str = "三年级"):
    """
    使用AI批改作文的流式版本，实时输出思考过程
    
    Args:
        text (str): 要批改的作文内容
        word_count (str): 作文字数要求
        grade (str): 年级
        
    Yields:
        Dict[str, Any]: 包含流式输出的字典
            - type: 'thinking' | 'result' | 'error'
            - content: 思考内容（仅当type='thinking'时）
            - corrections: 修改建议列表（仅当type='result'时）
            - error: 错误信息（仅当type='error'时）
    """
    if not text or not text.strip():
        yield {
            "type": "error",
            "error": "作文内容不能为空"
        }
        return
    
    try:
        # 获取阿里云配置
        provider = get_provider_config('aliyun')
        client = provider.get_llm()
        
        # 构建批改提示词
        grade_requirements = {
            "一年级": "简单语句，基本表达清楚",
            "二年级": "句子通顺，有基本的段落概念",
            "三年级": "语句通顺，有开头、中间、结尾",
            "四年级": "结构清楚，语言较为流畅",
            "五年级": "内容充实，语言生动",
            "六年级": "文章结构完整，语言准确生动",
            "初一": "观点明确，论证有条理",
            "初二": "语言表达准确，有一定文采",
            "初三": "思想深刻，语言优美，结构严谨"
        }
        
        grade_req = grade_requirements.get(grade, "语句通顺，内容完整")
        word_count_req = f"字数要求：{word_count}" if word_count != "不限字数" else "字数无特殊要求"
        
        prompt = f"""请你作为一名专业的语文老师，仔细批改以下{grade}学生的作文。

【作文要求】
- 年级：{grade}
- {word_count_req}
- 评判标准：{grade_req}

【批改要求】
1. 不要修改原文，只标出需要修改的地方
2. 请按照以下格式输出，每个部分都要包含：

## 总体评价
- 总体印象：（对整篇作文的总体评价）
- 优点：（列出作文的优点）
- 主要问题：（列出主要需要改进的问题）
- 建议得分：（按{grade}标准给出建议分数，满分100分）

## 病句修改
- 第X段第Y句："原文内容" → 问题：具体问题描述 → 建议：如何修改的建议

## 错别字修改  
- 第X段："错字" → 应为："正字" → 位置：具体位置描述

## 标点符号修改
- 第X段：问题描述 → 建议：正确用法

## 语言表达改进建议
- 建议内容（给出建议和例子，但不直接提供修改后的原文）

## 内容结构改进建议
- 建议内容

【作文内容】
{text}

请开始批改："""

        yield {
            "type": "thinking",
            "content": "正在连接AI模型..."
        }
        
        # 使用流式输出调用AI模型
        stream = client.chat.completions.create(
            model=AliyunModel.DEEPSEEK_R1.value,
            messages=[
                {"role": "system", "content": "你是一名专业的语文老师，负责批改学生作文。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000,
            stream=True
        )
        
        yield {
            "type": "thinking",
            "content": "AI开始思考批改方案..."
        }
        
        # 收集流式响应
        full_response = ""
        current_line = ""
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
                current_line += content
                
                # 实时显示AI的思考内容
                if content:
                    yield {
                        "type": "thinking",
                        "content": content
                    }
                
                # 当遇到换行符时，检查是否是完整的段落标题
                if "\n" in current_line:
                    lines = current_line.split("\n")
                    for line in lines[:-1]:  # 处理除最后一行外的所有行
                        if line.strip().startswith("##"):
                            section_name = line.strip().replace("##", "").strip()
                            if section_name:
                                yield {
                                    "type": "thinking",
                                    "content": f"\n📋 开始分析：{section_name}\n"
                                }
                    current_line = lines[-1]  # 保留最后一行继续处理
        
        yield {
            "type": "thinking",
            "content": "AI分析完成，正在整理批改结果..."
        }
        
        # 解析AI返回的批改结果
        corrections = parse_correction_response(full_response)
        
        # 发送完成信号
        yield {
            "type": "thinking",
            "content": "\n✅ AI批改完成！\n"
        }
        
        yield {
            "type": "result",
            "corrections": corrections,
            "raw_response": full_response
        }
        
    except Exception as e:
        yield {
            "type": "error",
            "error": f"AI批改失败：{str(e)}"
        }


def parse_correction_response(response: str) -> List[Dict[str, Any]]:
    """
    解析AI批改响应，提取各类修改建议
    
    Args:
        response (str): AI的批改响应
        
    Returns:
        List[Dict[str, Any]]: 解析后的修改建议列表
    """
    corrections = []
    
    # 按照不同的修改类型分割响应，使用更灵活的匹配
    sections = {
        "总体评价": [],
        "病句修改": [],
        "错别字修改": [],
        "标点符号修改": [],
        "语言表达改进建议": [],
        "内容结构改进建议": []
    }
    
    # 关键词映射，用于更智能的匹配
    section_keywords = {
        "总体评价": ["总体评价", "总体印象", "评价", "总结"],
        "病句修改": ["病句修改", "病句", "语法错误", "句子问题"],
        "错别字修改": ["错别字修改", "错别字", "错字", "别字", "字词错误"],
        "标点符号修改": ["标点符号修改", "标点符号", "标点", "符号"],
        "语言表达改进建议": ["语言表达改进建议", "语言表达", "表达建议", "语言改进"],
        "内容结构改进建议": ["内容结构改进建议", "内容结构", "结构建议", "内容改进"]
    }
    
    current_section = None
    lines = response.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 检查是否是新的分类标题 - 更智能的匹配
        if line.startswith('##') or line.startswith('#'):
            section_title = line.replace('##', '').replace('#', '').strip()
            
            # 尝试直接匹配
            if section_title in sections:
                current_section = section_title
                continue
            
            # 尝试关键词匹配
            for section_name, keywords in section_keywords.items():
                if any(keyword in section_title for keyword in keywords):
                    current_section = section_name
                    break
            continue
        
        # 如果是列表项，添加到当前分类
        if (line.startswith('-') or line.startswith('•') or line.startswith('*')) and current_section:
            correction_text = line[1:].strip()
            if correction_text:
                sections[current_section].append(correction_text)
        elif current_section and line and not line.startswith('【'):
            # 如果没有明确的列表标记，但有内容且在某个section中，也添加进去
            sections[current_section].append(line)
    
    # 将各个分类的内容整理成最终格式
    for section_name, items in sections.items():
        if items:
            corrections.append({
                "type": section_name,
                "items": items
            })
    
    # 如果没有解析到任何内容，尝试将整个响应作为总体评价
    if not corrections and response.strip():
        corrections.append({
            "type": "总体评价",
            "items": [response.strip()]
        })
    
    return corrections


if __name__ == "__main__":
    # 测试函数
    test_text = "你好，世界！Hello, world! 这是一个测试文本。This is a test."
    result = analyze_text(test_text)
    print(format_analysis_result(result)) 