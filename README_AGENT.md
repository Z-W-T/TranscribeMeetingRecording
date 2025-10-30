# 智能会议转录系统使用指南

## 功能概述

本系统提供了完整的会议录音转录和纪要生成解决方案，包括：

1. **语音转文字** - 支持使用 Whisper API 或本地 Whisper 模型
2. **会议纪要生成** - 自动生成结构化的会议纪要
3. **关键要点提取** - 快速提取会议要点
4. **摘要生成** - 生成会议简要摘要

## 项目结构

```
项目根目录/
├── agent/                        # 智能体模块
│   ├── __init__.py
│   ├── speech_recognition.py     # 语音识别模块
│   ├── meeting_minutes.py        # 会议纪要生成模块
│   └── transcription_agent.py    # 主智能体类
├── config/                       # 配置文件
│   ├── settings.py               # 系统配置
│   ├── prompts.yaml              # Prompt模板
│   └── prompts_manager.py        # Prompt管理
├── utils/                        # 工具函数
│   ├── api_client.py             # API客户端
│   └── __init__.py
├── data/                         # 数据文件夹
│   └── output/                   # 输出结果
├── main.py                       # 主入口
└── example_agent_usage.py        # 使用示例
```

## 安装依赖

### 基础依赖

```bash
pip install openai requests python-dotenv pyyaml
```

### 使用本地 Whisper（可选）

如果需要使用本地 Whisper 模型：

```bash
pip install openai-whisper
# 注意：首次使用时会自动下载模型
```

### 环境配置

创建 `.env` 文件：

```env
# DeepSeek API配置（用于生成会议纪要）
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_MODEL=Qwen/QwQ-32B

# OpenAI API配置（用于Whisper语音识别）
OPENAI_API_KEY=your_openai_api_key

# 智能体配置（可选）
SPEECH_ENGINE_TYPE=whisper_api  # 或 local_whisper
WHISPER_MODEL=whisper-1
OUTPUT_DIR=data/output
```

## 使用方法

### 方法1：使用智能体完整流程

```python
from dotenv import load_dotenv
from config.settings import Config
from agent.transcription_agent import TranscriptionAgent

load_dotenv()
config = Config()

# 创建智能转录代理
agent = TranscriptionAgent(
    speech_engine_type=config.AGENT_CONFIG["speech_engine_type"],
    api_settings=config.DEEPSEEK_SETTINGS
)

# 处理会议音频
results = agent.process_meeting(
    audio_input="path/to/meeting.mp3",
    generate_minutes=True,
    generate_summary=True,
    attendees=["张三", "李四", "王五"],
    meeting_topic="项目进度讨论"
)

# 保存结果
agent.save_results(results, output_path=config.AGENT_CONFIG["output_dir"])

# 打印结果
print("摘要:", results.get("summary"))
print("转录:", results.get("transcript"))
```

### 方法2：仅提取关键要点

```python
agent = TranscriptionAgent(
    speech_engine_type="whisper_api",
    api_settings=config.DEEPSEEK_SETTINGS
)

key_points = agent.extract_key_points("path/to/meeting.mp3")

for i, point in enumerate(key_points, 1):
    print(f"{i}. {point}")
```

### 方法3：仅进行语音转录

```python
agent = TranscriptionAgent(
    speech_engine_type="whisper_api",
    api_settings=config.DEEPSEEK_SETTINGS
)

transcript = agent.transcribe_audio("path/to/meeting.mp3")
print(transcript)
```

## 支持的音频格式

- MP3
- WAV
- M4A
- FLAC
- 其他 Whisper 支持的格式

## 输出文件说明

处理完成后，系统会在 `data/output` 目录生成以下文件：

- `transcript.txt` - 完整的会议转录文本
- `summary.txt` - 会议摘要
- `meeting_minutes.md` - 详细的会议纪要（Markdown格式）

## 配置说明

### 语音识别引擎

- **whisper_api**：使用 OpenAI 的 Whisper API（推荐，需要 API key）
- **local_whisper**：使用本地 Whisper 模型（首次使用需下载模型）

### 会议纪要生成

使用配置中的 `DEEPSEEK_SETTINGS` 来调用 LLM 生成会议纪要。项目已将 DeepSeek 调用封装为类 `DeepseekAPI`（位于 `utils/api_client.py`），示例：

```python
from config.settings import Config
from utils.api_client import DeepseekAPI

config = Config()
ds = DeepseekAPI(api_key=config.DEEPSEEK_SETTINGS.get("api_key"), model=config.DEEPSEEK_SETTINGS.get("model"))
prompt = "请为下面的会议转录生成摘要..."
summary = ds.call_api(prompt)
print(summary)
```

大多数使用场景无需直接调用 `DeepseekAPI`：主智能体（`TranscriptionAgent` / `MeetingMinutesGenerator`）会在内部使用 `api_settings` 自动构造客户端并调用 `call_api()`。

## 运行示例

```bash
# 运行主程序
python main.py

# 运行示例脚本
python example_agent_usage.py
```

## 模块说明

### TranscriptionAgent（主智能体）

核心智能体类，整合了语音识别和会议纪要生成功能。

**主要方法：**
- `transcribe_audio()` - 转录音频
- `process_meeting()` - 完整处理会议
- `extract_key_points()` - 提取关键要点
- `save_results()` - 保存结果

### SpeechRecognitionEngine（语音识别引擎）

支持多种语音识别后端。

**可用引擎：**
- `WhisperAPIEngine` - OpenAI Whisper API
- `LocalWhisperEngine` - 本地 Whisper 模型

### MeetingMinutesGenerator（会议纪要生成器）

负责生成会议摘要和详细纪要。

**主要方法：**
- `generate_summary()` - 生成摘要
- `generate_detailed_minutes()` - 生成详细纪要
- `extract_key_points()` - 提取关键要点

## 自定义配置

### 修改 Prompt 模板

编辑 `config/prompts.yaml` 来自定义会议纪要的生成格式：

```yaml
meeting_summary:
  system: "你是一名专业的会议记录员"
  template: |
    自定义的摘要生成模板
    {transcript}
```

### 修改输出格式

编辑 `agent/meeting_minutes.py` 中的 prompt 生成逻辑来自定义输出格式。

## 注意事项

1. 确保音频文件清晰、无严重噪音
2. 第一次使用本地 Whisper 需要下载模型（可能较慢）
3. API 调用会产生费用，请注意使用量
4. 长音频文件处理时间可能较长

## 故障排除

### OpenAI API 错误

确保 `.env` 文件中设置了正确的 `OPENAI_API_KEY`。

### DeepSeek API 错误

确保 `.env` 文件中设置了正确的 `DEEPSEEK_API_KEY`。

### 找不到音频文件

检查音频文件路径是否正确，支持相对路径和绝对路径。

### 本地 Whisper 模型下载失败

尝试使用 `whisper_api` 引擎，或手动下载模型。

