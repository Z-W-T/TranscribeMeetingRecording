"""
智能转录代理使用示例
展示如何使用TranscriptionAgent处理会议录音
"""
from dotenv import load_dotenv
from config.settings import Config
from agent.transcription_agent import TranscriptionAgent


def process_single_meeting():
    """处理单个会议音频文件"""
    load_dotenv()
    config = Config()
    
    # 创建智能转录代理
    agent = TranscriptionAgent(
        speech_engine_type=config.AGENT_CONFIG["speech_engine_type"],
        api_settings=config.DEEPSEEK_SETTINGS
    )
    
    # 音频文件路径
    audio_file = "data/sample_meeting.mp3"  # 替换为你的音频文件
    
    print("开始处理会议录音...")
    
    # 处理会议
    results = agent.process_meeting(
        audio_input=audio_file,
        generate_minutes=True,
        generate_summary=True,
        attendees=["张三", "李四"],
        meeting_topic="项目评审会议"
    )
    
    # 保存结果
    output_path = config.AGENT_CONFIG["output_dir"]
    agent.save_results(results, output_path=output_path)
    
    print(f"\n处理完成！结果已保存到 {output_path}")
    print("\n" + "=" * 60)
    print("会议摘要")
    print("=" * 60)
    print(results.get("summary", ""))
    print("\n" + "=" * 60)


def extract_key_points_only():
    """仅提取关键要点（不生成完整纪要）"""
    load_dotenv()
    config = Config()
    
    agent = TranscriptionAgent(
        speech_engine_type=config.AGENT_CONFIG["speech_engine_type"],
        api_settings=config.DEEPSEEK_SETTINGS
    )
    
    audio_file = "data/sample_meeting.mp3"
    
    print("正在提取关键要点...")
    
    key_points = agent.extract_key_points(audio_file)
    
    print("\n" + "=" * 60)
    print("关键要点")
    print("=" * 60)
    for i, point in enumerate(key_points, 1):
        print(f"{i}. {point}")


def simple_transcription_only():
    """仅进行语音转录，不生成纪要"""
    load_dotenv()
    config = Config()
    
    agent = TranscriptionAgent(
        speech_engine_type=config.AGENT_CONFIG["speech_engine_type"],
        api_settings=config.DEEPSEEK_SETTINGS
    )
    
    audio_file = "data/sample_meeting.mp3"
    
    print("正在转录音频...")
    
    transcript = agent.transcribe_audio(audio_file)
    
    print("\n" + "=" * 60)
    print("转录结果")
    print("=" * 60)
    print(transcript)
    
    # 保存到文件
    output_path = config.AGENT_CONFIG["output_dir"]
    from pathlib import Path
    Path(output_path).mkdir(parents=True, exist_ok=True)
    
    output_file = Path(output_path) / "transcript_only.txt"
    output_file.write_text(transcript, encoding="utf-8")
    
    print(f"\n转录结果已保存到: {output_file}")


if __name__ == "__main__":
    # 运行不同的示例（取消注释要运行的示例）
    
    # 示例1: 完整的会议处理和纪要生成
    # process_single_meeting()
    
    # 示例2: 仅提取关键要点
    # extract_key_points_only()
    
    # 示例3: 仅进行转录
    # simple_transcription_only()
    
    print("请取消注释上面的函数调用来运行示例")
    print("确保设置了正确的音频文件路径")

