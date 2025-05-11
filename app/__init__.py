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
            files = [f for f in os.listdir(disc_path) if f.lower().endswith('.mp3')]
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
        # 使用公共可访问的URL生成字幕
        srt_content = get_or_generate_subtitle(public_sample_url, book, disc, filename.replace('.mp3', ''))
        
        # 返回成功结果
        return jsonify({
            "success": True,
            "subtitle_url": f"/subtitles/{book}/{disc}/{filename.replace('.mp3', '')}.srt"
        })
    except Exception as e:
        # 返回错误信息
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 