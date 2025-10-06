# Changelog

所有重要的项目变更都记录在此文件中。

---

## [2025-10-06] 新增 OCR 作文拍照识别功能

### ✨ 新增功能
- **OCR 作文拍照识别**: 支持拍照或上传作文图片，自动识别文字
  - 访问路径: `/word-counter` (作文字数统计页面)
  - API 端点: `/api/ocr-recognize`

### 🎯 核心特性
- **多种输入方式**:
  - 📷 拍照识别（移动端直接调用摄像头）
  - 📁 上传图片文件（支持 JPG, PNG, BMP, GIF, WebP）
- **智能文字提取**:
  - 使用 Gemini 2.5 Flash 视觉 API
  - 支持手写和印刷文字识别
  - 智能保持段落和换行格式
  - 自动过滤页边涂鸦、折痕等干扰
- **多语言支持**:
  - 中文、英文、西班牙语
  - 根据选择的语言自动调整识别提示词
- **无缝集成**:
  - 识别结果自动填入文本框
  - 支持追加或替换现有内容
  - 自动触发字数统计
  - 可直接进行 AI 批改

### 🔧 技术实现
- **OCR 引擎**: Gemini 2.5 Flash Vision API
  - 上下文理解能力强
  - 手写识别准确度高
  - 成本低廉（$0.075/1M tokens）
- **核心文件**:
  - `app/llm/gemini_ocr.py` - Gemini Vision OCR 模块
  - `app/__init__.py` - 新增 `/api/ocr-recognize` 端点
  - `app/templates/word_counter.html` - 前端 OCR 界面
- **安全措施**:
  - 临时图片文件自动清理
  - 文件大小限制（最大 10MB）
  - 文件类型验证

### 📋 使用流程
1. 在作文字数统计页面点击"拍照"或"上传图片"
2. 选择/拍摄作文照片
3. 预览图片确认
4. 点击"识别文字"按钮
5. 等待 Gemini AI 识别（通常 2-5 秒）
6. 识别的文字自动填入编辑框
7. 可以继续编辑或直接进行 AI 批改

### 🎨 用户体验
- 图片预览功能
- 识别进度提示
- 详细的错误提示和建议
- 响应式设计，支持移动端
- 可折叠的 OCR 上传区域

### 🗑️ 代码清理
- 移除 `app/llm/volcano_ocr.py`（旧的火山引擎 OCR 方案）
- 移除 `volcengine` 依赖
- 简化技术栈，统一使用 Gemini API

### 📝 环境配置
- 无需新增环境变量
- 使用现有的 `GOOGLE_API_KEY`
- 与 AI 批改功能共用同一 API 密钥

### ✅ 已测试
- ✅ 图片上传和预览
- ✅ OCR 文字识别（中英文）
- ✅ 自动填充到文本框
- ✅ 字数统计触发
- ✅ 移动端拍照功能
- ✅ 临时文件清理

---

## [2025-10-06] 修复在线朗读功能并增强播放器控制

### 🐛 修复问题
- **修正所有音色ID为官方正确的Qwen3-TTS-Flash音色**
  - 移除无效音色：longxiaochun、zhibei、zhitian等
  - 添加正确音色：Cherry、Ethan、Jennifer、Ryan、Dylan等
  - 共12种可用音色（7种通用 + 5种方言/粤语）
- **解决 400 错误**：Voice not supported

### ✨ 新增功能
- **增强音频播放器控制**（参考英语跟读页面）
  - 播放/暂停按钮（图标自动切换）
  - 快进/后退3秒
  - 7级调速：0.5x, 0.75x, 1x, 1.25x, 1.5x, 2x, 3x
  - 实时速度显示
- **创建项目favicon图标**
  - SVG格式，融合音符和书本元素
  - 蓝金渐变配色，美观优雅
  - 应用到所有页面

### 🎨 用户体验改进
- 移除默认HTML5 audio controls
- 自定义播放器按钮，交互更友好
- 清空时重置播放速度为1x
- 更新功能说明，反映新增的播放控制

### 📝 音色列表更新

**通用音色（支持多语言）**:
- Cherry（芊悦）- 亲切自然女声
- Ethan（晨煦）- 标准普通话男声
- Nofish（不吃鱼）- 设计师风格
- Jennifer（詹妮弗）- 电影质感女声
- Ryan（甜茶）- 高能量男声
- Katerina（卡捷琳娜）- 成熟女声
- Elias（墨讲师）- 学术风男声

**方言音色**:
- Dylan - 北京话
- Sunny - 四川话
- Jada - 上海话
- Rocky - 粤语（幽默风）
- Kiki - 香港粤语

### ✅ 已测试
- ✅ 所有音色API调用正常
- ✅ 播放器控制功能完整
- ✅ 调速功能（0.5x-3x）
- ✅ 快进后退功能
- ✅ Favicon在所有页面显示

---

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

## [2025-09-16] Gemini流式传输支持与API修复

### 🚀 重大更新
- **完全修复Gemini模型连接问题**: 解决"新的 gemini model报错"问题
- **真正的流式传输支持**: 实现Gemini API的真正流式输出
- **智能流式解析**: 支持JSON数组流格式的实时解析

### 🔧 技术改进
- **自定义Gemini客户端**: 创建GeminiClient包装器，兼容OpenAI接口
- **流式端点优化**: 使用streamGenerateContent端点实现真正的流式传输
- **增量JSON解析**: 实现逐步解析JSON数组流的算法
- **API配置修复**: 修正GeminiProvider的base_url配置

### 📝 详细变更
- 修复providers.py中的GeminiProvider配置
- 实现真正的流式响应处理，支持逐块文本输出
- 添加JSON数组流解析器，处理Gemini特有的响应格式
- 保持向后兼容性，同步API仍正常工作

### 🧪 测试验证
- 同步API：✅ 正常工作
- 流式API：✅ 真正的实时输出
- 错误处理：✅ 完善的异常处理机制

---

## [2025-09-16] 多语言作文批改系统升级

### 主要更新
- **多语言支持**: 新增英语和西班牙语作文批改功能
- **智能模型选择**: 根据服务器环境自动选择最优LLM模型
- **界面优化**: 调整布局，新增AI思考过程可视化面板
- **前端修复**: 修复JavaScript错误，完善用户体验

### 技术改进
- 添加Google Gemini 2.5 Flash Lite模型支持
- 实现基于hostname的智能LLM提供者选择
- 优化多语言批改提示词和响应解析
- 重构前端界面布局和交互逻辑

### 详细功能说明
- AI作文批改功能详情请参考: [AI_CORRECTION_GUIDE.md](AI_CORRECTION_GUIDE.md)

---

## [2025-03-25] 优化字幕质量

### 改进
- 修正标点符号、大小写和说话人颜色区分
- 提升字幕阅读体验

---

## [2025-03-24] 异步字幕优化

### 新增功能
- 实现异步字幕优化功能，提升用户体验
- 字幕在后台自动优化，不影响播放

---

## [2025-03-23] 移动端优化

### 改进
- 移除24点游戏页面自动聚焦行为
- 优化移动端用户体验，避免虚拟键盘弹出

---

## [2025-03-22] 部署优化

### 修复
- 修复Fabric部署超时问题
- 改进部署流程的稳定性

---

## [2025-03-21] AI批改优化

### 改进
- 全面优化AI批改流式响应处理
- 提升实时反馈的流畅度

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
- **Web 服务器**: Gunicorn (2 workers, 180s timeout)
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
