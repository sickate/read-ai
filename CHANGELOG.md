# Changelog

# 更新日志 / Change Log

## 2025-10-06 - 统一响应式Header设计

### 🎨 界面优化
- **统一Header组件**: 重新设计 `_navigation.html` 为完整的响应式header
- **品牌视觉升级**: 添加"超能力训练场"品牌标识和火箭图标
- **现代化设计**: 紫色渐变背景 (#667eea → #764ba2)，提升视觉层次

### 📱 响应式支持
- **Desktop布局**: 水平导航栏，菜单靠右对齐
- **iPad优化**: 汉堡菜单 + 可折叠导航
- **iPhone适配**: 紧凑布局，触摸友好的按钮尺寸

### ✨ 交互体验
- **当前页面高亮**: 自动标记用户所在页面
- **悬停动画**: 菜单项上移效果和半透明背景
- **品牌可点击**: Logo点击返回首页
- **图标支持**: 所有菜单项配备FontAwesome图标

### 🔧 技术改进
- 移除各页面独立的h1标题，避免重复
- 统一使用 `current_page` 参数控制高亮状态
- 基于Bootstrap 5 navbar组件，确保跨浏览器兼容性
- 优化页面间距和布局一致性

### 📄 影响文件
- `app/templates/_navigation.html` - 重构为完整header组件
- `app/templates/index.html` - Header置顶，移除独立标题
- `app/templates/tts.html` - Header置顶，移除独立标题
- `app/templates/game_24.html` - Header置顶，移除独立标题
- `app/templates/word_counter.html` - Header置顶，移除独立标题

---

## 2025-09-16 - Gemini流式传输支持与API修复

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

## 2025-09-16 - 多语言作文批改系统升级

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

## 历史版本

### 2025-03-25 - 优化字幕质量
- 修正标点符号、大小写和说话人颜色区分

## 2025-03-24 - 异步字幕优化
- 实现异步字幕优化功能，提升用户体验

## 2025-03-23 - 移动端优化
- 移除24点游戏页面自动聚焦行为，优化移动端用户体验

## 2025-03-22 - 部署优化
- 修复Fabric部署超时问题

## 2025-03-21 - AI批改优化
- 全面优化AI批改流式响应处理

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
