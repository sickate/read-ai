import os
import requests
import time
import json
import re
import pathlib
from dotenv import load_dotenv

load_dotenv()   

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

def generate_subtitle_for_mp3(audio_url, output_path=None, language="en"):
    """
    为MP3文件生成SRT字幕并保存到指定路径
    
    Args:
        audio_url: 音频文件URL
        output_path: 字幕文件保存路径，如果为None则仅返回字幕内容而不保存
        language: 语言代码，默认为英语
        
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

def get_or_generate_subtitle(audio_url, book_name, disc_no, track_name, base_dir="app/static/subtitles"):
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
    srt_content = generate_subtitle_for_mp3(audio_url, subtitle_path)
    
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