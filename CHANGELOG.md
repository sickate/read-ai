# Changelog

## [2025-10-06] 新增在线朗读功能

### 新增功能
- **在线朗读 (Text-to-Speech)**: 支持中英文文本转语音，多种音色可选
  - 访问路径: `/tts`
  - API 端点: `/api/text-to-speech`

### 技术实现
- **API 提供商**: 阿里云 DashScope Qwen3-TTS
  - 模型: `qwen3-tts-flash`
  - 成本: 0.8元/万字符
  - 音质: 接近真人，自然韵律

- **音色支持** (8种常用音色):
  - Cherry - 亲切自然（女声）
  - longxiaochun - 阳光积极
  - zhibei - 可靠成熟
  - zhitian - 温柔知性
  - longwan - 二次元虚拟女友
  - longxiaoxia - 活泼少女
  - longjing - 沉稳专业（男声）
  - longxiaobei - 北京音

- **语言支持** (8种语言):
  - 自动检测 (Auto)
  - 中文 (Chinese)
  - 英文 (English)
  - 日语 (Japanese)
  - 韩语 (Korean)
  - 西班牙语 (Spanish)
  - 法语 (French)
  - 德语 (German)

### 核心文件
- `app/llm/tts_helper.py` - TTS 辅助模块
  - `text_to_speech()` - 文本转语音核心函数
  - `get_available_voices()` - 获取可用音色列表
  - `get_available_languages()` - 获取可用语言列表

- `app/__init__.py` - 新增路由
  - `@app.route('/tts')` - 在线朗读页面
  - `@app.route('/api/text-to-speech')` - TTS API 接口

- `app/templates/tts.html` - 前端页面
  - Bootstrap 5 响应式设计
  - 实时字符计数 (0-5000)
  - 音频播放器集成
  - 自动播放生成的音频

- `app/templates/_navigation.html` - 导航栏更新
  - 添加"在线朗读"入口

### 功能特性
1. **文本输入**: 支持最多 5000 字符
2. **中英混合**: 可在同一文本中混合使用中英文，自动切换发音
3. **实时反馈**: 字符计数、加载状态、错误提示
4. **音频播放**: 生成的音频 URL 24 小时有效，支持在线播放
5. **响应式设计**: 支持桌面和移动设备

### 依赖更新
- 升级 `dashscope` 从 1.23.2 到 >=1.24.6
  - 新版本支持 `qwen3-tts-flash` 模型
  - 修复 MultiModalConversation.call() API 调用

### 测试验证
- ✅ TTS helper 模块单元测试
- ✅ API 接口功能测试
- ✅ Web 界面完整流程测试
- ✅ 中英混合文本朗读测试

### 使用示例

#### Python API 调用
```python
from app.llm.tts_helper import text_to_speech

result = text_to_speech(
    text="Hello! 你好，这是一个测试。",
    voice="Cherry",
    language="Auto"
)

if result['success']:
    print(f"Audio URL: {result['audio_url']}")
```

#### HTTP API 调用
```bash
curl -X POST http://localhost:5010/api/text-to-speech \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello test","voice":"Cherry","language":"Auto"}'
```

### 注意事项
- 需要配置 `DASHSCOPE_API_KEY` 环境变量
- 音频 URL 有效期为 24 小时
- 单次请求最大支持 5000 字符
- 建议文本语言与 `language_type` 参数一致以获得最佳效果

---

## 项目约定和规范

### 开发环境
- **虚拟环境管理**: 使用 `uv` 管理 `.venv` 虚拟环境
- **运行端口**: 5010 (本地开发)
- **自动重载**: 开发模式支持代码修改自动生效
- **不需要额外启动实例**: 项目已在后台运行

### 代码组织
- **主应用**: `app/__init__.py` - Flask 应用主文件，包含所有路由
- **LLM 模块**: `app/llm/` - LLM 提供商配置和 AI 功能
  - `providers.py` - 多 LLM 提供商配置
  - `volcano_audio.py` - 音频字幕生成
  - `tts_helper.py` - 文本转语音
- **工具函数**: `utils/` - 核心工具函数
  - `text_helper.py` - 文本分析和 AI 作文批改
- **模板**: `app/templates/` - HTML 模板
  - `_navigation.html` - 共用导航栏
- **静态文件**: `app/static/`
  - `audios/` - 音频文件存储
  - `subtitles/` - 字幕文件存储

### API 提供商
项目支持多个 LLM/AI 提供商:
- **Aliyun (阿里云)**: 主要提供商
  - DashScope API
  - 模型: deepseek-r1, qwen-max, qwen3-tts-flash 等
  - 需要 `DASHSCOPE_API_KEY`
- **OpenAI**: GPT-4, GPT-4o
- **SiliconFlow**: DeepSeek-V3, Qwen
- **XAI**: Grok-2
- **Google Gemini**: Gemini 2.0 Flash

### 开发约定
1. **优先编辑现有文件**: 不要轻易创建新文件，优先在现有文件中扩展功能
2. **不主动创建文档**: 除非用户明确要求，否则不创建 README 或 .md 文档
3. **响应式设计**: 使用 Bootstrap 5，确保移动端兼容
4. **导航一致性**: 所有页面使用 `_navigation.html` 共用导航栏
5. **当前页面标记**: 通过 `current_page` 参数高亮当前页面

### 部署
- **部署工具**: Fabric (`fab deploy`)
- **目标服务器**: maru
- **应用目录**: `/var/www/read-ai/`
- **Web 服务器**: Gunicorn (2 workers, 120s timeout)
- **软链接目录**: audios, subtitles, logs

### 环境变量
所有 API 密钥存储在 `.env` 文件中:
- `DASHSCOPE_API_KEY` - 阿里云 API Key
- `OPENAI_API_KEY` - OpenAI API Key
- `SILICON_FLOW_API_KEY` - SiliconFlow API Key
- `XAI_API_KEY` - XAI API Key
- `GOOGLE_API_KEY` - Google Gemini API Key

### Git 规范
- 提交前确保功能测试通过
- 提交信息使用中文描述
- 包含改动的核心功能说明
