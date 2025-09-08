import os
import requests
import time
import json
import re
import pathlib
from dotenv import load_dotenv

load_dotenv()

# 导入LLM providers
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.llm.providers import get_provider_config, AliyunModel   

def log_time(func):
    def wrapper(*args, **kw):
        begin_time = time.time()
        result = func(*args, **kw)
        print('total cost time = {time}'.format(time=time.time() - begin_time))
        return result
    return wrapper

class VolcanoAudioProvider():
    """VolcanoAudio提供者配置"""

    def __init__(self):
        self.__api_base__ = 'https://openspeech.bytedance.com/api/v1/vc'
        self.__api_key__ = os.getenv("VOLCANO_AUDIO_API_KEY")
        self.__appid__ = os.getenv("VOLCANO_AUDIO_APPID")
        self.__access_token__ = os.getenv("VOLCANO_AUDIO_ACCESS_TOKEN")

    @log_time
    def get_subtitles(self, file_url: str, language: str = 'en'):
        """
        获取音频字幕原始数据
        
        Args:
            file_url: 音频文件的URL
            language: 语言代码，默认为英语('en')
            
        Returns:
            API返回的原始响应数据
        """
        response = requests.post(
                    '{base_url}/submit'.format(base_url=self.__api_base__),
                    params=dict(
                        appid=self.__appid__,
                        language=language,
                        use_itn='True',
                        use_capitalize='True',
                        max_lines=1,
                        words_per_line=15,
                    ),
                    json={
                        'url': file_url,
                    },
                    headers={
                        'content-type': 'application/json',
                        'Authorization': 'Bearer; {}'.format(self.__access_token__)
                    }
                )
        print('Submit response = {}'.format(response.text))
        
        if response.status_code != 200:
            raise Exception(f"Error submitting audio transcription job: {response.text}")
        
        response_json = response.json()
        if response_json.get('message') != 'Success':
            raise Exception(f"Failed to submit audio transcription job: {response_json}")

        job_id = response_json['id']
        
        response = requests.get(
                '{base_url}/query'.format(base_url=self.__api_base__),
                params=dict(
                    appid=self.__appid__,
                    id=job_id,
                ),
                headers={
                'Authorization': 'Bearer; {}'.format(self.__access_token__)
                }
        )
            
        if response.status_code != 200:
            print(f"Error checking job status: {response.text}")
                
        return response.json()
            
    def convert_to_srt(self, subtitles_data):
        """
        将Volcano API返回的字幕数据转换为SRT格式
        
        Args:
            subtitles_data: API返回的字幕数据
            
        Returns:
            SRT格式的字幕内容
        """
        try:
            utterances = subtitles_data.get('utterances', [])
            if not utterances:
                return "1\n00:00:00,000 --> 00:00:10,000\n[未能识别有效内容]"
            
            srt_parts = []
            for i, utterance in enumerate(utterances):
                # 确保有文本内容
                text = utterance.get('text', '').strip()
                if not text:
                    continue
                
                # 获取开始和结束时间（毫秒）
                # API返回的时间单位是毫秒
                start_ms = int(float(utterance.get('start_time', 0)))
                end_ms = int(float(utterance.get('end_time', 0)))
                
                # 转换为SRT时间格式 (HH:MM:SS,mmm)
                start_time = self._format_time(start_ms)
                end_time = self._format_time(end_ms)
                
                # 添加SRT条目
                srt_parts.append(f"{i+1}\n{start_time} --> {end_time}\n{text}\n")
            
            if not srt_parts:
                return "1\n00:00:00,000 --> 00:00:10,000\n[未能识别有效内容]"
                
            return "\n".join(srt_parts)
            
        except Exception as e:
            print(f"Error converting to SRT: {str(e)}")
            return "1\n00:00:00,000 --> 00:00:10,000\n[字幕转换错误]"
    
    def _format_time(self, ms):
        """
        将毫秒转换为SRT时间格式 (HH:MM:SS,mmm)
        
        Args:
            ms: 毫秒时间
            
        Returns:
            格式化的时间字符串
        """
        try:
            if isinstance(ms, str):
                ms = float(ms)
                
            # 确保ms是一个非负数
            ms = max(0, ms)
            
            # 转换为时、分、秒和毫秒
            total_seconds = int(ms / 1000)
            milliseconds = int(ms % 1000)
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            # 格式化为 HH:MM:SS,mmm
            return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
        except Exception as e:
            print(f"Error formatting time: {str(e)}")
            return "00:00:00,000"

def parse_srt_to_entries(srt_content):
    """
    解析SRT字幕内容为结构化数据（支持说话人标记）
    
    Args:
        srt_content: SRT格式字幕内容
        
    Returns:
        List[Dict]: 字幕条目列表，每个条目包含index、start_time、end_time、text、speaker
    """
    entries = []
    if not srt_content or not srt_content.strip():
        return entries
    
    # SRT格式正则表达式
    pattern = r'(\d+)\n([\d:,]+)\s+-->\s+([\d:,]+)\n((?:.*\n?)*?)(?=\n\d+\n|$)'
    matches = re.findall(pattern, srt_content.strip() + '\n', re.MULTILINE)
    
    for match in matches:
        index, start_time, end_time, text = match
        text_content = text.strip()
        speaker = None
        
        # 检查文本是否包含说话人标记
        speaker_match = re.match(r'\[([ABC])\]\s*(.*)', text_content)
        if speaker_match:
            speaker = speaker_match.group(1)
            text_content = speaker_match.group(2)
        
        entries.append({
            'index': int(index),
            'start_time': start_time.strip(),
            'end_time': end_time.strip(), 
            'text': text_content,
            'speaker': speaker
        })
    
    return entries

def entries_to_srt(entries):
    """
    将结构化字幕数据转换为SRT格式（支持说话人信息）
    
    Args:
        entries: 字幕条目列表，可能包含说话人信息
        
    Returns:
        str: SRT格式字幕内容，说话人信息嵌入到文本中
    """
    srt_parts = []
    for i, entry in enumerate(entries):
        if entry['text'].strip():  # 只保留有文本内容的条目
            text_content = entry['text'].strip()
            
            # 如果有说话人信息，将其嵌入到文本开头
            if entry.get('speaker'):
                text_content = f"[{entry['speaker']}] {text_content}"
            
            srt_parts.append(f"{i+1}\n{entry['start_time']} --> {entry['end_time']}\n{text_content}\n")
    
    return "\n".join(srt_parts)

def optimize_subtitles_with_llm(srt_content, max_retries=2):
    """
    使用LLM优化字幕，将碎片化的短句合并为完整的语义单元
    
    Args:
        srt_content: 原始SRT字幕内容
        max_retries: 最大重试次数
        
    Returns:
        str: 优化后的SRT字幕内容
    """
    if not srt_content or not srt_content.strip():
        return srt_content
    
    try:
        # 解析原始字幕
        entries = parse_srt_to_entries(srt_content)
        if len(entries) < 2:  # 如果字幕条目太少，不需要优化
            return srt_content
            
        print(f"Original subtitle entries: {len(entries)}")
        
        # 准备给LLM的文本格式
        text_for_llm = "原始字幕条目:\n"
        for i, entry in enumerate(entries):
            text_for_llm += f"{i+1}. [{entry['start_time']} --> {entry['end_time']}] {entry['text']}\n"
        
        # 构建LLM提示词
        prompt = f"""你是一个专业的英语字幕优化专家。请将下面碎片化的英语字幕优化成自然流畅的对话字幕。

【核心要求】:
1. 将相邻的短句合并为完整的语义单元，但不要跨越不同说话人
2. 添加正确的标点符号（逗号、句号、问号、感叹号）
3. 处理大小写（句首大写、专有名词大写）
4. 识别对话中的说话人切换，为不同说话人添加标记

【合并规则】:
- 同一说话人的连续短句可以合并
- 问句和答句通常来自不同说话人，不要合并
- 呼唤人名、打招呼通常是对话的开始
- 保持对话的自然节奏和停顿

【说话人标记】:
- 为不同的说话人添加 [A]、[B]、[C] 等标记
- 第一个说话人标记为 [A]，第二个为 [B]，以此类推
- 判断说话人切换的线索：问答关系、称呼转换、话题转换

【输出格式】:
序号. [开始时间 --> 结束时间] [说话人] 文本内容

【示例】:
原始: 1. [00:00:00,000 --> 00:00:01,000] What's
原始: 2. [00:00:01,000 --> 00:00:02,000] wrong
原始: 3. [00:00:02,500 --> 00:00:04,000] I can't find
原始: 4. [00:00:04,000 --> 00:00:05,500] my mom

优化: 1. [00:00:00,000 --> 00:00:02,000] [A] What's wrong?
优化: 2. [00:00:02,500 --> 00:00:05,500] [B] I can't find my mom.

{text_for_llm}

请输出优化后的字幕条目:"""

        # 获取LLM配置并调用
        provider = get_provider_config('aliyun')
        client = provider.get_llm()
        
        for attempt in range(max_retries + 1):
            try:
                response = client.chat.completions.create(
                    model=AliyunModel.QWEN_PLUS_LATEST.value,  # 使用较便宜的模型
                    messages=[
                        {"role": "system", "content": "你是一个专业的英语字幕优化专家，擅长将碎片化的字幕合并为完整句子。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,  # 低温度确保一致性
                    max_tokens=2000
                )
                
                llm_response = response.choices[0].message.content
                print(f"LLM response received (attempt {attempt + 1})")
                
                # 解析LLM的响应
                optimized_entries = parse_llm_response(llm_response)
                if optimized_entries:
                    optimized_srt = entries_to_srt(optimized_entries)
                    print(f"Optimized subtitle entries: {len(optimized_entries)}")
                    return optimized_srt
                else:
                    print(f"Failed to parse LLM response on attempt {attempt + 1}")
                    if attempt < max_retries:
                        time.sleep(1)  # 等待1秒后重试
                    continue
                    
            except Exception as e:
                print(f"LLM call failed on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries:
                    time.sleep(2)  # 等待2秒后重试
                    continue
                else:
                    break
        
        print("LLM optimization failed, returning original subtitles")
        return srt_content
        
    except Exception as e:
        print(f"Error in optimize_subtitles_with_llm: {str(e)}")
        return srt_content

def parse_llm_response(llm_response):
    """
    解析LLM返回的字幕优化结果（支持说话人标记）
    
    Args:
        llm_response: LLM的响应文本
        
    Returns:
        List[Dict]: 解析后的字幕条目列表，包含说话人信息
    """
    entries = []
    lines = llm_response.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 匹配格式: 序号. [时间1 --> 时间2] [说话人] 文本内容
        match = re.match(r'(\d+)\.\s*\[([^\]]+)\s+-->\s+([^\]]+)\]\s*\[([^\]]+)\]\s*(.+)', line)
        if match:
            index, start_time, end_time, speaker, text = match.groups()
            entries.append({
                'index': int(index),
                'start_time': start_time.strip(),
                'end_time': end_time.strip(),
                'text': text.strip(),
                'speaker': speaker.strip()
            })
            continue
            
        # 兼容旧格式: 序号. [时间1 --> 时间2] 文本内容 （无说话人标记）
        match_old = re.match(r'(\d+)\.\s*\[([^\]]+)\s+-->\s+([^\]]+)\]\s*(.+)', line)
        if match_old:
            index, start_time, end_time, text = match_old.groups()
            entries.append({
                'index': int(index),
                'start_time': start_time.strip(),
                'end_time': end_time.strip(),
                'text': text.strip(),
                'speaker': None  # 无说话人信息
            })
    
    return entries

def generate_subtitle_for_mp3(audio_url, output_path=None, language="en", enable_llm_optimization=True):
    """
    为MP3文件生成SRT字幕并保存到指定路径
    
    Args:
        audio_url: 音频文件URL
        output_path: 字幕文件保存路径，如果为None则仅返回字幕内容而不保存
        language: 语言代码，默认为英语
        enable_llm_optimization: 是否启用LLM优化，默认True
        
    Returns:
        生成的SRT字幕内容
    """
    provider = VolcanoAudioProvider()
    
    try:
        # 获取字幕数据
        subtitles_data = provider.get_subtitles(audio_url, language)
        
        print(subtitles_data)
        
        # 转换为SRT格式
        srt_content = provider.convert_to_srt(subtitles_data)
        
        # 如果启用LLM优化，则进行字幕优化
        if enable_llm_optimization and srt_content and language == "en":
            print("Optimizing subtitles with LLM...")
            optimized_srt = optimize_subtitles_with_llm(srt_content)
            if optimized_srt != srt_content:  # 只有优化成功时才替换
                srt_content = optimized_srt
                print("Subtitles optimized successfully")
            else:
                print("LLM optimization skipped or failed, using original subtitles")
        
        # 如果指定了输出路径，保存SRT文件
        if output_path:
            # 确保目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 写入SRT文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            print(f"SRT subtitle saved to: {output_path}")
        
        return srt_content
        
    except Exception as e:
        print(f"Error generating subtitle: {str(e)}")
        return None

def get_or_generate_subtitle(audio_url, book_name, disc_no, track_name, base_dir="app/static/subtitles", enable_llm_optimization=True):
    """
    获取或生成字幕，如果字幕文件不存在则生成新的
    
    Args:
        audio_url: 音频文件URL
        book_name: 书籍名称
        disc_no: 光盘编号
        track_name: 音轨名称
        base_dir: 字幕文件基础目录
        
    Returns:
        字幕文件路径
    """
    # 处理文件名，移除不合法字符
    cleaned_track_name = re.sub(r'[\\/*?:"<>|]', '', track_name)
    # 构建字幕文件路径
    subtitle_dir = os.path.join(base_dir, book_name, disc_no)
    subtitle_path = os.path.join(subtitle_dir, f"{cleaned_track_name}.srt")
    
    # 检查字幕文件是否已存在
    if os.path.exists(subtitle_path):
        print(f"Subtitle already exists: {subtitle_path}")
        with open(subtitle_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    # 生成新的字幕
    print(f"Generating subtitle for: {audio_url}")
    srt_content = generate_subtitle_for_mp3(audio_url, subtitle_path, enable_llm_optimization=enable_llm_optimization)
    
    return srt_content

if __name__ == '__main__':
    # 示例：生成字幕
    audio_url = 'https://read-ai.instap.net/static/audios/ET3/disc1/04%20%E6%9B%B2%E7%9B%AE%204.mp3'
    book_name = "ET3"
    disc_no = "1"
    track_name = "04 曲目 4"
    
    # 删除现有字幕文件（如果存在），以强制重新生成
    subtitle_dir = os.path.join("static/subtitles", book_name, f"disc{disc_no}")
    subtitle_path = os.path.join(subtitle_dir, f"{track_name}.srt")
    if os.path.exists(subtitle_path):
        print(f"Removing existing subtitle file: {subtitle_path}")
        os.remove(subtitle_path)
    
    # 直接调用生成字幕函数以查看完整响应
    provider = VolcanoAudioProvider()
    try:
        response_data = provider.get_subtitles(audio_url, "en")
        print("Raw API Response:")
        print(json.dumps(response_data, indent=2, ensure_ascii=False))
        
        # 现在尝试生成字幕
        srt_content = get_or_generate_subtitle(audio_url, book_name, disc_no, track_name)
        print("\nGenerated SRT content:")
        print(srt_content)
    except Exception as e:
        print(f"Error: {str(e)}")