# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an English learning platform focused on elementary school English textbook audio content. The application provides:

- **Audio Player**: Stream elementary school English textbook audio files (ET3 series)
- **Subtitle Generation**: AI-powered subtitle generation using Alibaba Cloud's audio analysis
- **Text Analysis**: Word count and text analysis tools for Chinese essays  
- **AI Essay Correction**: Real-time AI-powered essay correction with streaming feedback
- **24-Point Math Game**: Interactive mathematical puzzle game

## Development Commands

### Running the Application
```bash
# Development server
python app/__init__.py

# Production deployment using Fabric
fab deploy
```

### Testing
```bash
# Test AI correction functionality
python test_ai_correction.py

# Test word counter functionality  
python test_word_counter.py
```

### Dependencies
```bash
# Install dependencies
pip install -r requirements.txt
```

## Architecture

### Core Structure
- **`app/__init__.py`**: Main Flask application with all routes and core functionality
- **`app/llm/`**: LLM provider configurations and audio processing
  - **`providers.py`**: Multi-provider LLM configuration (Aliyun, OpenAI, SiliconFlow, etc.)
  - **`volcano_audio.py`**: Audio subtitle generation using Alibaba Cloud services
- **`utils/`**: Core utilities
  - **`text_helper.py`**: Text analysis and AI essay correction with streaming support
- **`app/templates/`**: HTML templates with responsive Bootstrap design
- **`app/static/audios/`**: Audio file storage (ET3 textbook series)
- **`app/static/subtitles/`**: Generated SRT subtitle files

### Key Features

#### LLM Integration
The app supports multiple LLM providers configured in `app/llm/providers.py`:
- **Alibaba Cloud**: Primary provider using DashScope API (deepseek-r1, qwen-max models)
- **OpenAI**: GPT-4, GPT-4o models
- **SiliconFlow**: DeepSeek-V3, Qwen models  
- **XAI**: Grok-2 models
- **Google Gemini**: Gemini 2.0 Flash models

#### Audio Processing
- Supports MP3/M4A audio files organized by book/disc structure
- Real-time subtitle generation using Alibaba Cloud's Paraformer-v2 model
- Audio files served directly through Flask routes

#### Streaming AI Responses
The essay correction feature uses streaming responses for real-time feedback:
- **Regular API**: `/api/correct-essay` for standard responses
- **Streaming API**: `/api/correct-essay-stream` for real-time AI thinking process display

### Environment Variables
Required environment variables (set in `.env`):
```bash
DASHSCOPE_API_KEY=your_alibaba_cloud_api_key
OPENAI_API_KEY=your_openai_api_key  
SILICON_FLOW_API_KEY=your_siliconflow_api_key
XAI_API_KEY=your_xai_api_key
GOOGLE_API_KEY=your_google_api_key
```

### Deployment
Uses Fabric for deployment automation:
- **Target server**: maru (remote_host='maru')
- **App directory**: `/var/www/read-ai/`
- **Gunicorn configuration**: 2 workers, 120s timeout, debug logging
- **Symlinked directories**: audios, subtitles, logs

## Important Implementation Notes

### AI Essay Correction
- Minimum text length: 50 characters
- Supports multiple grade levels (一年级 to 初三)
- Categories corrections into: grammar errors, typos, punctuation, language improvement, content structure
- **Enhanced Streaming Support**:
  - Intelligent fallback: Mobile devices and slow connections automatically use stable mode
  - Dynamic timeouts: 3 minutes for mobile, 2 minutes for desktop
  - Retry mechanisms: Up to 3 attempts with exponential backoff
  - Heartbeat monitoring: Prevents connection timeouts during long AI processing
  - Network status detection: Warns users about connectivity issues
  - Error recovery: Detailed error messages with actionable suggestions

### Audio Subtitle Generation  
- Generates SRT format subtitles using Alibaba Cloud's audio recognition
- Requires publicly accessible audio URLs for cloud processing
- Caches generated subtitles locally

### Security Considerations
- No user authentication system currently implemented
- File uploads restricted to audio formats
- API keys stored in environment variables only
- Input validation for text analysis and essay correction
- 项目运行在本地 5010 端口且可以自动 reload, 任何修改能直接生效. 不需要额外启动 flask 实例来测试