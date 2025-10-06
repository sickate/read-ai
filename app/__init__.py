from flask import Flask, render_template, url_for, request, jsonify, send_file, Response
import os
import json
import threading
import time
from app.llm.volcano_audio import get_or_generate_subtitle, optimize_subtitles_with_llm
from app.llm.tts_helper import text_to_speech, get_available_voices, get_available_languages
import requests
from utils.text_helper import analyze_text, ai_correct_essay, ai_correct_essay_stream
from app.game_24 import game_24

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
    return render_template('index.html', audio_tree=audio_tree, current_page='home')

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

# 全局变量跟踪优化任务状态
optimization_tasks = {}

@app.route('/api/optimize-subtitle', methods=['POST'])
def optimize_subtitle():
    """
    触发字幕异步优化任务
    """
    data = request.json
    book = data.get('book')
    disc = data.get('disc')
    filename = data.get('filename')
    
    if not all([book, disc, filename]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    # 创建任务唯一标识
    task_key = f"{book}_{disc}_{filename}"
    
    # 检查是否已有优化文件
    filename_without_ext = os.path.splitext(filename)[0]
    optimized_subtitle_path = os.path.join(SUBTITLE_ROOT, book, disc, f"{filename_without_ext}.optimized.srt")
    
    if os.path.exists(optimized_subtitle_path):
        return jsonify({
            "success": True,
            "status": "completed",
            "optimized_url": f"/subtitles/{book}/{disc}/{filename_without_ext}.optimized.srt"
        })
    
    # 检查原始字幕是否存在
    original_subtitle_path = os.path.join(SUBTITLE_ROOT, book, disc, f"{filename_without_ext}.srt")
    if not os.path.exists(original_subtitle_path):
        return jsonify({"error": "Original subtitle not found"}), 404
    
    # 检查是否正在处理中
    if task_key in optimization_tasks and optimization_tasks[task_key]['status'] == 'processing':
        return jsonify({
            "success": True,
            "status": "processing",
            "message": "Optimization already in progress"
        })
    
    # 标记任务开始
    optimization_tasks[task_key] = {
        'status': 'processing',
        'start_time': time.time()
    }
    
    def optimize_subtitle_task():
        try:
            # 读取原始字幕
            with open(original_subtitle_path, 'r', encoding='utf-8') as f:
                original_srt = f.read()
            
            # 调用LLM优化
            optimized_srt = optimize_subtitles_with_llm(original_srt)
            
            # 保存优化后的字幕
            if optimized_srt and optimized_srt != original_srt:
                os.makedirs(os.path.dirname(optimized_subtitle_path), exist_ok=True)
                with open(optimized_subtitle_path, 'w', encoding='utf-8') as f:
                    f.write(optimized_srt)
                
                optimization_tasks[task_key] = {
                    'status': 'completed',
                    'end_time': time.time(),
                    'optimized_url': f"/subtitles/{book}/{disc}/{filename_without_ext}.optimized.srt"
                }
                print(f"Subtitle optimization completed for {task_key}")
            else:
                optimization_tasks[task_key] = {
                    'status': 'failed',
                    'end_time': time.time(),
                    'error': 'LLM optimization failed or returned unchanged content'
                }
                print(f"Subtitle optimization failed for {task_key}")
                
        except Exception as e:
            optimization_tasks[task_key] = {
                'status': 'failed',
                'end_time': time.time(),
                'error': str(e)
            }
            print(f"Subtitle optimization error for {task_key}: {str(e)}")
    
    # 启动后台线程
    thread = threading.Thread(target=optimize_subtitle_task)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "success": True,
        "status": "processing",
        "task_id": task_key,
        "message": "Optimization started"
    })

@app.route('/api/check-optimized-subtitle')
def check_optimized_subtitle():
    """
    检查字幕优化状态
    """
    book = request.args.get('book')
    disc = request.args.get('disc')
    filename = request.args.get('filename')
    
    if not all([book, disc, filename]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    task_key = f"{book}_{disc}_{filename}"
    filename_without_ext = os.path.splitext(filename)[0]
    
    # 检查优化文件是否存在
    optimized_subtitle_path = os.path.join(SUBTITLE_ROOT, book, disc, f"{filename_without_ext}.optimized.srt")
    
    if os.path.exists(optimized_subtitle_path):
        return jsonify({
            "success": True,
            "status": "completed",
            "optimized_url": f"/subtitles/{book}/{disc}/{filename_without_ext}.optimized.srt"
        })
    
    # 检查任务状态
    if task_key in optimization_tasks:
        task = optimization_tasks[task_key]
        return jsonify({
            "success": True,
            "status": task['status'],
            "error": task.get('error'),
            "optimized_url": task.get('optimized_url')
        })
    
    return jsonify({
        "success": True,
        "status": "not_started"
    })

@app.route('/word-counter')
def word_counter():
    """作文字数统计页面"""
    return render_template('word_counter.html', current_page='word-counter')

@app.route('/api/analyze-text', methods=['POST'])
def api_analyze_text():
    """
    分析文本的API接口
    接收POST请求，包含text参数
    返回文本分析结果
    """
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({
                "success": False,
                "error": "缺少text参数"
            }), 400
        
        text = data['text']
        language = data.get('language', 'zh')  # 默认中文

        if not text.strip():
            return jsonify({
                "success": False,
                "error": "文本内容不能为空"
            }), 400

        # 使用新的多语言分析函数
        from utils.text_helper import analyze_text_multilingual
        result = analyze_text_multilingual(text, language)
        
        return jsonify({
            "success": True,
            "result": result
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/correct-essay', methods=['POST'])
def api_correct_essay():
    """
    AI批改作文的API接口
    接收POST请求，包含text参数
    返回AI批改结果
    """
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({
                "success": False,
                "error": "缺少text参数"
            }), 400
        
        text = data['text']
        if not text.strip():
            return jsonify({
                "success": False,
                "error": "作文内容不能为空"
            }), 400
        
        # 检查文本长度，避免过短的文本
        if len(text.strip()) < 50:
            return jsonify({
                "success": False,
                "error": "作文内容过短，请输入至少50个字符的作文"
            }), 400
        
        # 获取额外参数
        word_count = data.get('word_count', '不限字数')
        grade = data.get('grade', '三年级')
        language = data.get('language', 'zh')  # 默认中文

        # 使用text_helper中的ai_correct_essay函数批改作文
        result = ai_correct_essay(text, word_count, grade, language)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"服务器错误：{str(e)}"
        }), 500


@app.route('/api/correct-essay-stream', methods=['POST'])
def api_correct_essay_stream():
    """
    AI批改作文的流式API接口
    使用fetch stream来实现实时输出，增加了更好的错误处理和超时管理
    """
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({
                "success": False,
                "error": "缺少text参数"
            }), 400
        
        text = data['text']
        if not text.strip():
            return jsonify({
                "success": False,
                "error": "作文内容不能为空"
            }), 400
        
        # 检查文本长度，避免过短的文本
        if len(text.strip()) < 50:
            return jsonify({
                "success": False,
                "error": "作文内容过短，请输入至少50个字符的作文"
            }), 400
        
        # 使用生成器函数来实现流式输出
        def generate_stream():
            import time
            try:
                # 发送开始信号
                yield f"data: {json.dumps({'type': 'thinking', 'content': '开始分析作文内容...'})}\n\n"
                
                # 获取额外参数
                word_count = data.get('word_count', '不限字数')
                grade = data.get('grade', '三年级')
                language = data.get('language', 'zh')  # 默认中文

                # 添加心跳机制，防止连接超时
                last_heartbeat = time.time()
                heartbeat_interval = 30  # 30秒发送一次心跳

                # 使用流式方式调用AI
                result = ai_correct_essay_stream(text, word_count, grade, language)
                
                for chunk in result:
                    current_time = time.time()
                    
                    # 发送心跳信号，防止连接超时
                    if current_time - last_heartbeat > heartbeat_interval:
                        yield f"data: {json.dumps({'type': 'thinking', 'content': '⏳ AI正在深度分析中...'})}\n\n"
                        last_heartbeat = current_time
                    
                    if chunk['type'] == 'thinking':
                        yield f"data: {json.dumps(chunk)}\n\n"
                        last_heartbeat = current_time  # 更新心跳时间
                    elif chunk['type'] == 'result':
                        yield f"data: {json.dumps(chunk)}\n\n"
                        break
                    elif chunk['type'] == 'error':
                        yield f"data: {json.dumps(chunk)}\n\n"
                        break
                        
            except GeneratorExit:
                # 客户端断开连接
                yield f"data: {json.dumps({'type': 'error', 'error': '客户端连接中断'})}\n\n"
            except Exception as e:
                error_msg = str(e)
                if "timeout" in error_msg.lower():
                    yield f"data: {json.dumps({'type': 'error', 'error': 'AI服务响应超时，请稍后重试'})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'error', 'error': f'处理出错：{error_msg}'})}\n\n"
        
        response = Response(
            generate_stream(),
            mimetype='text/plain',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Content-Type': 'text/plain; charset=utf-8',
                'X-Accel-Buffering': 'no',  # 禁用nginx缓冲，立即发送数据
                'Access-Control-Allow-Origin': '*',  # 允许跨域（如果需要）
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        )
        
        # 设置响应超时为5分钟
        response.timeout = 300
        
        return response
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"服务器错误：{str(e)}"
        }), 500

@app.route('/game-24')
def game_24_page():
    """24点游戏页面"""
    return render_template('game_24.html', current_page='game-24')

@app.route('/api/game-24/new-game', methods=['POST'])
def new_24_game():
    """开始新的24点游戏"""
    try:
        data = request.json or {}
        game_mode = data.get('mode', '24')  # '24' 或 '60'
        only_solvable = data.get('only_solvable', False)
        
        # 根据模式确定卡牌数量和目标值
        if game_mode == '60':
            num_cards = 5
            target = 60
        else:
            num_cards = 4
            target = 24
        
        # 生成卡牌
        if only_solvable:
            cards = game_24.generate_solvable_cards(num_cards, target)
        else:
            cards = game_24.generate_cards(num_cards)
        
        # 获取解答（如果需要）
        solutions = game_24.solve_24(cards, target) if only_solvable else []
        
        return jsonify({
            "success": True,
            "cards": cards,
            "target": target,
            "has_solution": len(solutions) > 0,
            "solutions": solutions[:3]  # 最多返回3个解答
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/game-24/verify', methods=['POST'])
def verify_24_answer():
    """验证24点游戏答案"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "缺少请求数据"}), 400
        
        expression = data.get('expression', '').strip()
        cards = data.get('cards', [])
        target = data.get('target', 24)
        
        if not expression or not cards:
            return jsonify({"success": False, "error": "缺少表达式或卡牌"}), 400
        
        # 验证答案
        is_correct = game_24.verify_answer(expression, cards, target)
        
        return jsonify({
            "success": True,
            "is_correct": is_correct
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/game-24/solutions', methods=['POST'])
def get_24_solutions():
    """获取24点游戏的解答"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "缺少请求数据"}), 400

        cards = data.get('cards', [])
        target = data.get('target', 24)

        if not cards:
            return jsonify({"success": False, "error": "缺少卡牌"}), 400

        # 获取解答
        solutions = game_24.solve_24(cards, target)

        return jsonify({
            "success": True,
            "solutions": solutions,
            "has_solution": len(solutions) > 0
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/tts')
def tts_page():
    """在线朗读页面"""
    voices = get_available_voices()
    languages = get_available_languages()
    return render_template('tts.html', current_page='tts', voices=voices, languages=languages)

@app.route('/api/text-to-speech', methods=['POST'])
def api_text_to_speech():
    """
    文本转语音的API接口
    接收POST请求，包含text, voice, language参数
    返回音频URL或音频数据
    """
    try:
        data = request.json
        if not data or 'text' not in data:
            return jsonify({
                "success": False,
                "error": "缺少text参数"
            }), 400

        text = data['text']
        if not text.strip():
            return jsonify({
                "success": False,
                "error": "文本内容不能为空"
            }), 400

        # 检查文本长度限制
        if len(text) > 5000:
            return jsonify({
                "success": False,
                "error": "文本过长，最多支持5000个字符"
            }), 400

        # 获取参数
        voice = data.get('voice', 'Cherry')
        language = data.get('language', 'Auto')

        # 调用TTS服务
        result = text_to_speech(text=text, voice=voice, language=language, stream=False)

        if result['success']:
            return jsonify({
                "success": True,
                "audio_url": result['audio_url'],
                "format": result.get('format', 'wav')
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', '未知错误')
            }), 500

    except ValueError as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"服务器错误：{str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(debug=True) 