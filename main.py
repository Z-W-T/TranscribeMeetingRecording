from dotenv import load_dotenv
from config.settings import Config
from agent.transcription_agent import TranscriptionAgent


def example_meeting_transcription():
    """示例：处理会议录音并生成纪要"""
    load_dotenv()
    config = Config()
    
    # 创建智能转录代理
    agent = TranscriptionAgent(
        speech_engine_type=config.AGENT_CONFIG["speech_engine_type"],
        api_settings=config.DEEPSEEK_SETTINGS
    )
    print('智能转录代理已创建，开始处理会议录音...')
    
    # 处理会议音频：从配置中读取（优先使用 config.AGENT_CONFIG['audio_input']，可通过环境变量 AUDIO_INPUT 覆盖）
    audio_file = config.AGENT_CONFIG.get("audio_input")
    print(f"Using audio file: {audio_file}")
    
    results = agent.process_meeting(
        audio_input=audio_file,
        generate_minutes=True,
        generate_summary=True,
        attendees=["张三", "李四", "王五"],
        meeting_topic="项目进度讨论"
    )
    
    # 保存结果到文件
    agent.save_results(results=results, output_path=config.AGENT_CONFIG["output_dir"])

    # 打印结果
    print("=" * 60)
    print("会议转录完成")
    print("=" * 60)
    print("\n【摘要】\n")
    print(results.get("summary", ""))
    print("\n【完整转录】\n")
    print(results.get("transcript", ""))
        
    # except Exception as e:
    #     # 捕获并输出任何异常
    #     print(f"错误：处理音频时发生异常: {e}")
    #     # 如需调试完整堆栈信息，可取消注释下一行
    #     # import traceback; traceback.print_exc()


def example_key_points_extraction():
    """示例：提取关键要点"""
    load_dotenv()
    config = Config()
    
    agent = TranscriptionAgent(
        speech_engine_type=config.AGENT_CONFIG["speech_engine_type"],
        api_settings=config.DEEPSEEK_SETTINGS
    )
    
    audio_file = "data/dialogue_recording.mp3"
    
    try:
        key_points = agent.extract_key_points(audio_file)
        
        print("=" * 60)
        print("关键要点提取")
        print("=" * 60)
        for i, point in enumerate(key_points, 1):
            print(f"{i}. {point}")
            
    except FileNotFoundError:
        print(f"错误：找不到音频文件 {audio_file}")


if __name__ == "__main__":
    # 运行示例
    example_meeting_transcription()
    
    # 取消注释以下行来运行关键要点提取示例
    # example_key_points_extraction()