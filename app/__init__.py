from flask import Flask, render_template, url_for, request, jsonify, send_file
import os
from app.llm.volcano_audio import get_or_generate_subtitle
import requests

app = Flask(__name__)

AUDIO_ROOT = os.path.join(app.static_folder, 'audios')
SUBTITLE_ROOT = os.path.join(app.static_folder, 'subtitles')

@app.route('/')
def index():
    audio_tree = {}
    for book in os.listdir(AUDIO_ROOT):
        book_path = os.path.join(AUDIO_ROOT, book)
        if not os.path.isdir(book_path):
            continue
        audio_tree[book] = {}
        for disc in os.listdir(book_path):
            disc_path = os.path.join(book_path, disc)
            if not os.path.isdir(disc_path):
                continue
            files = [f for f in os.listdir(disc_path) if f.lower().endswith(('.mp3', '.m4a'))]
            files.sort()
            audio_tree[book][disc] = files
    return render_template('index.html', audio_tree=audio_tree)

@app.route('/audio/<path:filename>')
def serve_audio(filename):
    """直接提供音频文件，而不是通过静态文件路径"""
    return send_file(os.path.join(AUDIO_ROOT, filename))

@app.route('/subtitles/<path:filename>')
def serve_subtitle(filename):
    """直接提供字幕文件，而不是通过静态文件路径"""
    subtitle_path = os.path.join(SUBTITLE_ROOT, filename)
    if os.path.exists(subtitle_path):
        return send_file(subtitle_path)
    else:
        return "Subtitle not found", 404

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    """
    处理音频文件上传
    支持本地文件上传和URL导入
    """
    try:
        # 获取表单数据
        book = request.form.get('book')
        disc = request.form.get('disc')
        audio_name = request.form.get('audioName')
        audio_source = request.form.get('audioSource')
        
        # 验证必要字段
        if not all([book, disc, audio_name]):
            return jsonify({"success": False, "error": "缺少必要参数"}), 400
        
        # 确保目录存在
        book_path = os.path.join(AUDIO_ROOT, book)
        disc_path = os.path.join(book_path, disc)
        
        os.makedirs(book_path, exist_ok=True)
        os.makedirs(disc_path, exist_ok=True)
        
        # 处理字幕目录
        subtitle_book_path = os.path.join(SUBTITLE_ROOT, book)
        subtitle_disc_path = os.path.join(subtitle_book_path, disc)
        
        os.makedirs(subtitle_book_path, exist_ok=True)
        os.makedirs(subtitle_disc_path, exist_ok=True)
        
        # 根据音频来源处理
        if audio_source == 'local':
            # 本地文件上传
            if 'audioFile' not in request.files:
                return jsonify({"success": False, "error": "没有收到音频文件"}), 400
                
            audio_file = request.files['audioFile']
            if not audio_file.filename:
                return jsonify({"success": False, "error": "没有选择文件"}), 400
            
            # 从上传文件中获取后缀名
            original_ext = os.path.splitext(audio_file.filename)[1].lower()
            
            # 检查用户提供的文件名是否已经有后缀
            if not os.path.splitext(audio_name)[1]:
                # 如果没有后缀，添加从上传文件中获取的后缀
                if original_ext:
                    audio_name = f"{audio_name}{original_ext}"
                else:
                    # 如果上传文件没有后缀，默认使用.mp3
                    audio_name = f"{audio_name}.mp3"
            
            # 文件保存路径
            file_path = os.path.join(disc_path, audio_name)
                
            # 保存文件
            audio_file.save(file_path)
            
        elif audio_source == 'url':
            # URL导入
            audio_url = request.form.get('audioUrl')
            if not audio_url:
                return jsonify({"success": False, "error": "URL为空"}), 400
            
            # 从URL中提取文件名和后缀
            url_filename = os.path.basename(audio_url.split('?')[0])
            url_ext = os.path.splitext(url_filename)[1].lower()
            
            # 检查用户提供的文件名是否已经有后缀
            if not os.path.splitext(audio_name)[1]:
                # 如果没有后缀，添加从URL中获取的后缀
                if url_ext:
                    audio_name = f"{audio_name}{url_ext}"
                else:
                    # 如果URL没有明确的后缀，默认使用.mp3
                    audio_name = f"{audio_name}.mp3"
            
            # 文件保存路径
            file_path = os.path.join(disc_path, audio_name)
                
            # 下载文件
            response = requests.get(audio_url, stream=True)
            if response.status_code != 200:
                return jsonify({"success": False, "error": f"下载失败，状态码: {response.status_code}"}), 400
                
            # 保存文件
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        else:
            return jsonify({"success": False, "error": "不支持的音频来源类型"}), 400
            
        # 更新音频树（不需要手动更新，下次刷新页面会自动加载）
        
        return jsonify({
            "success": True,
            "message": "文件上传成功",
            "path": f"/audio/{book}/{disc}/{audio_name}"
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/generate-subtitle', methods=['POST'])
def generate_subtitle():
    """
    为指定的音频文件生成字幕
    接收POST请求，包含book, disc, filename参数
    """
    data = request.json
    book = data.get('book')
    disc = data.get('disc')
    filename = data.get('filename')
    
    if not all([book, disc, filename]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    # 对于本地开发环境，我们需要使用可公开访问的URL
    # 这里我们使用一个替代URL，您需要替换为真实的可公开访问的音频URL
    # 例如，您可以使用已经上传到某个公共服务器的音频文件
    # 或者您可以将本地文件临时上传到一个文件共享服务
    
    # 以下是使用公共示例URL的例子
    # 实际使用时需要替换为您自己的文件
    # 对于测试，您可以使用一些公共可访问的音频样本
    public_sample_url = "https://read-ai.instap.net/static/audios/{book}/{disc}/{filename}".format(
        book=book, disc=disc, filename=filename
    )
    
    try:
        # 获取不带扩展名的文件名
        filename_without_ext = os.path.splitext(filename)[0]
        
        # 使用公共可访问的URL生成字幕
        srt_content = get_or_generate_subtitle(public_sample_url, book, disc, filename_without_ext)
        
        # 返回成功结果
        return jsonify({
            "success": True,
            "subtitle_url": f"/subtitles/{book}/{disc}/{filename_without_ext}.srt"
        })
    except Exception as e:
        # 返回错误信息
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 