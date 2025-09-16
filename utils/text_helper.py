import re
from typing import Dict, Any, List
import os
import sys
import time
import socket

# 添加项目根目录到路径，以便导入app模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.llm.providers import get_provider_config, AliyunModel, GeminiModel


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


def get_smart_llm_provider(language: str = "zh"):
    """
    根据主机名和语言智能选择LLM提供者和模型

    Args:
        language (str): 语言代码 "zh", "en", "es"

    Returns:
        tuple: (provider, model)
    """
    hostname = socket.gethostname().lower()

    # 如果是maru服务器，使用阿里云模型（因为没有VPN无法访问Gemini）
    if hostname == "maru":
        provider = get_provider_config('aliyun')
        model = AliyunModel.DEEPSEEK_R1.value
    else:
        # 其他环境使用Gemini（轻量且多语言支持好）
        try:
            provider = get_provider_config('google')
            model = GeminiModel.GEMINI_2_5_FLASH_LITE.value
        except:
            # 如果Gemini配置有问题，回退到阿里云
            provider = get_provider_config('aliyun')
            model = AliyunModel.DEEPSEEK_R1.value

    return provider, model


def analyze_text_multilingual(text: str, language: str = "zh") -> Dict[str, Any]:
    """
    多语言文本分析，统计不同语言的单位

    Args:
        text (str): 要分析的文本
        language (str): 语言代码 "zh", "en", "es"

    Returns:
        Dict[str, Any]: 包含统计结果的字典
            - main_count: 主要计数单位（中文字数或英文/西语单词数）
            - punctuation: 标点符号数
            - total_chars: 总字符数
            - language: 语言标识
    """
    if not text:
        return {
            "main_count": 0,
            "punctuation": 0,
            "total_chars": 0,
            "language": language
        }

    # 统计标点符号（通用）
    chinese_punctuation_pattern = r'[\u3000-\u303f\uff00-\uffef]'
    english_punctuation_pattern = r'[!\"#$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~]'
    chinese_punctuation_count = len(re.findall(chinese_punctuation_pattern, text))
    english_punctuation_count = len(re.findall(english_punctuation_pattern, text))
    punctuation = chinese_punctuation_count + english_punctuation_count

    # 总字符数
    total_chars = len(text)

    if language == "zh":
        # 中文：统计汉字数
        chinese_pattern = r'[\u4e00-\u9fff]'
        main_count = len(re.findall(chinese_pattern, text))
    else:
        # 英语/西语：统计单词数
        # 移除标点符号，按空格分割单词
        words = re.findall(r'\b\w+\b', text.lower())
        main_count = len(words)

    return {
        "main_count": main_count,
        "punctuation": punctuation,
        "total_chars": total_chars,
        "language": language
    }


def ai_correct_essay(text: str, word_count: str = "不限字数", grade: str = "三年级", language: str = "zh") -> Dict[str, Any]:
    """
    使用AI批改作文，检查语法、错别字、标点符号等问题

    Args:
        text (str): 要批改的作文内容
        word_count (str): 作文字数要求
        grade (str): 年级
        language (str): 语言代码 "zh", "en", "es"

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
        # 智能选择LLM提供者
        provider, model = get_smart_llm_provider(language)
        client = provider.get_llm()

        # 根据语言选择批改提示词
        prompt = get_correction_prompt(text, language, word_count, grade)

        # 调用AI模型
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": get_system_prompt(language)},
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


def get_system_prompt(language: str) -> str:
    """
    根据语言返回系统提示词

    Args:
        language (str): 语言代码 "zh", "en", "es"

    Returns:
        str: 系统提示词
    """
    if language == "en":
        return "You are a professional English teacher who helps Chinese students improve their English writing skills."
    elif language == "es":
        return "You are a professional Spanish teacher who helps Chinese students learn Spanish writing."
    else:
        return "你是一名专业的语文老师，负责批改学生作文。"


def get_correction_prompt(text: str, language: str, word_count: str, grade: str) -> str:
    """
    根据语言生成批改提示词

    Args:
        text (str): 作文内容
        language (str): 语言代码 "zh", "en", "es"
        word_count (str): 字数要求
        grade (str): 年级

    Returns:
        str: 批改提示词
    """
    if language == "en":
        return get_english_correction_prompt(text, word_count, grade)
    elif language == "es":
        return get_spanish_correction_prompt(text, word_count, grade)
    else:
        return get_chinese_correction_prompt(text, word_count, grade)


def get_chinese_correction_prompt(text: str, word_count: str, grade: str) -> str:
    """生成中文作文批改提示词"""
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

    return f"""请你作为一名专业的语文老师，仔细批改以下{grade}学生的作文。

【作文要求】
- 年级：{grade}
- {word_count_req}
- 评判标准：{grade_req}

【批改要求】
1. 不要修改原文，只标出需要修改的地方
2. 严格按照以下格式输出，每个 ## 标题下必须有 - 开头的列表项：

【输出格式样例】
## 总体评价
- 总体印象：文章主题明确，结构基本清晰
- 优点：开头点题，内容较充实
- 主要问题：存在语法错误和用词不当
- 建议得分：75分

## 病句修改
- 第1段第2句："我们学校发生了很多的变化" → 问题：语序不当 → 建议：改为"我们学校发生了很多变化"

## 错别字修改
- 第2段："即使"写成了"既使" → 应为："即使" → 位置：第2段第3行

## 标点符号修改
- 第1段：句号使用错误 → 建议：疑问句应用问号

## 语言表达改进建议
- 建议使用更丰富的词汇来表达情感
- 可以适当运用修辞手法增强表达效果

## 内容结构改进建议
- 段落之间缺乏过渡，建议添加承接词语
- 结尾可以更好地呼应开头

【作文内容】
{text}

请严格按照上述格式批改："""


def get_english_correction_prompt(text: str, word_count: str, grade: str) -> str:
    """生成英语作文批改提示词"""
    grade_levels = {
        "一年级": "初学者水平 - 基础句型和简单词汇",
        "二年级": "入门级 - 一般现在时和基础句子结构",
        "三年级": "初级 - 过去时、将来时和基础段落",
        "四年级": "初中级 - 复杂句式和词汇扩展",
        "五年级": "中级 - 文章结构（开头、正文、结尾）",
        "六年级": "中高级 - 高级词汇和多样句型",
        "初一": "中级进阶 - 中等语法和文章组织",
        "初二": "高级 - 高级语法和写作技巧",
        "初三": "高级进阶 - 复杂写作和精准表达"
    }

    level_desc = grade_levels.get(grade, "中级水平")
    word_req = f"单词数要求：{word_count}个单词" if word_count != "不限字数" else "无特殊单词数要求"

    return f"""作为一名专业的英语老师，请仔细批改以下中国学生的英语作文。请用中文进行批改和建议，帮助学生更好地理解。

【作文要求】
- 水平：{level_desc}
- {word_req}

【批改要求】
1. 不要重写作文，只指出需要改进的地方
2. 用中文解释英语错误，便于学生理解
3. 重点关注中国学生常见的英语错误（如冠词、时态、中式英语等）
4. 严格按照以下格式输出，每个 ## 标题下必须有 - 开头的列表项：

【输出格式样例】
## 总体评价
- 总体印象：文章主题明确，但存在语法错误
- 优点：词汇量不错，逻辑较清晰
- 主要问题：时态使用不准确，中式英语表达较多
- 建议得分：B级

## 语法错误修正
- 第1段第1句："I am study English" → 错误类型：时态错误 → 建议：应为"I am studying English"或"I study English"

## 词汇使用改进
- 第2段："very good" → 建议用词："excellent" → 说明：避免重复使用简单词汇

## 句子结构问题
- 第1段：句子过长难理解 → 建议：拆分为两个简单句

## 中式英语修正
- "I very like it" → 地道表达："I like it very much" → 解释：副词位置要正确

## 语言表达改进建议
- 尝试使用更多连接词来增强逻辑性
- 避免重复使用相同的句型结构

## 内容结构改进建议
- 开头段可以更明确地点出主题
- 结尾段需要更好地总结全文

【学生作文】
{text}

请严格按照上述格式批改："""


def get_spanish_correction_prompt(text: str, word_count: str, grade: str) -> str:
    """生成西班牙语作文批改提示词"""
    grade_levels = {
        "一年级": "初学者 - 基本词汇和现在时",
        "二年级": "入门级 - 简单句型和基础语法",
        "三年级": "初级 - 过去时和将来时的使用",
        "四年级": "初中级 - 复杂句型和词汇扩展",
        "五年级": "中级 - 文章结构和段落组织",
        "六年级": "中高级 - 高级语法和表达技巧",
        "初一": "高级初学 - 虚拟式和复杂时态",
        "初二": "中级进阶 - 高级写作技巧",
        "初三": "高级 - 复杂写作和文学表达"
    }

    level_desc = grade_levels.get(grade, "中级水平")
    word_req = f"字数要求：{word_count}个单词" if word_count != "不限字数" else "无特殊字数要求"

    return f"""作为一名专业的西班牙语老师，请仔细批改以下中国学生的西班牙语作文。请用中文进行批改和建议，帮助学生更好地理解。

【作文要求】
- 水平：{level_desc}
- {word_req}

【批改要求】
1. 不要重写作文，只指出需要改进的地方
2. 用中文解释语法错误，便于学生理解
3. 重点关注中国学生常见的西班牙语错误（如性别一致、动词变位等）
4. 严格按照以下格式输出，每个 ## 标题下必须有 - 开头的列表项：

【输出格式样例】
## 总体评价
- 总体印象：文章内容基本完整，但语法错误较多
- 优点：词汇使用较丰富，主题明确
- 主要问题：动词变位和性别一致性错误频繁
- 建议得分：C级

## 语法错误修正
- 第1段第2句："Yo es estudiante" → 错误类型：动词变位错误 → 建议：应为"Yo soy estudiante"（第一人称单数用soy）

## 词汇使用改进
- 第2段："casa pequeño" → 建议用词："casa pequeña" → 说明：形容词性别要与名词一致

## 语序和句法问题
- 第1段：语序不自然 → 建议：调整为西班牙语标准语序

## 性别和数的一致性
- "la problema" → 正确形式："el problema" → 说明：problema是阳性词

## 表达建议
- 尝试使用更多的连接词丰富句子结构
- 注意动词时态的统一性

## 内容结构建议
- 段落之间缺乏逻辑连接
- 结尾可以更好地呼应开头

【学生作文】
{text}

请严格按照上述格式批改："""


def ai_correct_essay_stream(text: str, word_count: str = "不限字数", grade: str = "三年级", language: str = "zh"):
    """
    使用AI批改作文的流式版本，实时输出思考过程

    Args:
        text (str): 要批改的作文内容
        word_count (str): 作文字数要求
        grade (str): 年级
        language (str): 语言代码 "zh", "en", "es"

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
        # 智能选择LLM提供者
        provider, model = get_smart_llm_provider(language)
        client = provider.get_llm(timeout=180)  # 增加到3分钟超时
        
        # 根据语言生成批改提示词
        prompt = get_correction_prompt(text, language, word_count, grade)

        # 显示使用的模型信息
        provider, model = get_smart_llm_provider(language)
        model_info = f"使用模型：{model}"
        yield {
            "type": "thinking",
            "content": f"正在连接AI模型...（{model_info}）"
        }
        
        # 使用流式输出调用AI模型，增加错误重试机制
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                stream = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": get_system_prompt(language)},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=3000,  # 增加token限制
                    stream=True,
                    timeout=180  # 3分钟超时
                )
                break  # 成功创建，退出重试循环
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    raise e
                yield {
                    "type": "thinking",
                    "content": f"连接超时，正在重试 ({retry_count}/{max_retries})..."
                }
                time.sleep(2)  # 等待2秒后重试
        
        yield {
            "type": "thinking",
            "content": "AI开始思考批改方案..."
        }
        
        # 收集流式响应，增加超时和心跳检测
        full_response = ""
        current_line = ""
        last_chunk_time = time.time()
        chunk_timeout = 30  # 30秒内没有新chunk则认为超时
        
        try:
            for chunk in stream:
                current_time = time.time()
                
                # 检查chunk超时
                if current_time - last_chunk_time > chunk_timeout:
                    yield {
                        "type": "thinking",
                        "content": "⚠️ 数据传输缓慢，正在等待AI响应..."
                    }
                
                last_chunk_time = current_time
                
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
                        
        except Exception as stream_error:
            yield {
                "type": "thinking",
                "content": f"流式传输中断: {str(stream_error)}，正在处理已接收的内容..."
            }
            # 继续处理已接收的内容，不直接抛出异常
        
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
        import traceback
        error_msg = str(e)
        
        # 提供更详细的错误信息
        if "timeout" in error_msg.lower():
            yield {
                "type": "error", 
                "error": "AI服务响应超时，请稍后重试。建议：1) 检查网络连接 2) 缩短作文长度 3) 稍后再试"
            }
        elif "connection" in error_msg.lower():
            yield {
                "type": "error",
                "error": "网络连接问题，请检查网络状态后重试"
            }
        elif "rate limit" in error_msg.lower():
            yield {
                "type": "error",
                "error": "请求过于频繁，请稍等片刻后重试"
            }
        else:
            yield {
                "type": "error",
                "error": f"AI批改失败：{error_msg}"
            }
        
        # 记录详细错误日志（仅在开发环境）
        import os
        if os.getenv('DEBUG') == 'True':
            print(f"Stream error traceback: {traceback.format_exc()}")


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

    # 关键词映射，用于更智能的匹配（支持中英文）
    section_keywords = {
        "总体评价": ["总体评价", "总体印象", "评价", "总结", "Overall Evaluation", "General Assessment", "Overall", "Evaluation"],
        "病句修改": ["病句修改", "病句", "语法错误", "句子问题", "语法错误修正", "语序和句法问题", "句子结构问题", "Grammar Corrections", "Grammar", "Sentence Issues", "Sentence Structure"],
        "错别字修改": ["错别字修改", "错别字", "错字", "别字", "字词错误", "词汇使用改进", "性别和数的一致性", "Vocabulary Improvements", "Vocabulary", "Word Choice"],
        "标点符号修改": ["标点符号修改", "标点符号", "标点", "符号", "Punctuation", "Punctuation Corrections"],
        "语言表达改进建议": ["语言表达改进建议", "语言表达", "表达建议", "语言改进", "中式英语修正", "表达建议", "Language Expression Tips", "Expression", "Language Tips", "Natural English"],
        "内容结构改进建议": ["内容结构改进建议", "内容结构", "结构建议", "内容改进", "内容结构建议", "Content & Organization Tips", "Organization", "Structure", "Content Tips"]
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

            # 移除可能的装饰符号 **bold** 等
            import re
            section_title_clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', section_title)
            section_title_clean = section_title_clean.strip()

            # 尝试直接匹配
            if section_title_clean in sections:
                current_section = section_title_clean
                continue

            # 尝试关键词匹配（忽略大小写）
            for section_name, keywords in section_keywords.items():
                if any(keyword.lower() in section_title_clean.lower() for keyword in keywords):
                    current_section = section_name
                    break
            continue
        
        # 如果是列表项，添加到当前分类
        if (line.startswith('-') or line.startswith('•') or line.startswith('*') or line.startswith('–')) and current_section:
            correction_text = line[1:].strip()
            if correction_text:
                sections[current_section].append(correction_text)
        elif current_section and line and not line.startswith('【') and not line.startswith('##'):
            # 如果没有明确的列表标记，但有内容且在某个section中，也添加进去
            # 但排除以下情况：标题行、空行、特殊标记行
            if line.strip() and not line.startswith('请') and not line.startswith('注意'):
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