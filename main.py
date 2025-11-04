from dotenv import load_dotenv
from config.settings import Config
from agent.transcription_agent import TranscriptionAgent

def example_meeting_transcription(agent, config):
    """示例：处理会议录音转录为文本"""
    audio_file = config.AGENT_CONFIG.get("audio_input")
    print(f"Using audio file: {audio_file}")
    print('开始转录文本...')

    transcript = agent.transcribe_audio(audio_input=audio_file)

    # 打印结果
    print("=" * 60)
    print("会议转录文本")
    print("=" * 60) 
    print("\n【转录文本】\n")
    print(f'{transcript}')

    return transcript

def example_meeting_summary_generation(agent, config):
    """示例：处理会议录音并生成纪要"""
    # 处理会议音频：从配置中读取（优先使用 config.AGENT_CONFIG['audio_input']，可通过环境变量 AUDIO_INPUT 覆盖）
    audio_file = config.AGENT_CONFIG.get("audio_input")
    print(f"Using audio file: {audio_file}")
    print('开始提取摘要...')
    
    summary = agent.generate_summary(audio_input=audio_file,)

    # 打印结果
    print("=" * 60)
    print("会议摘要生成完成")
    print("=" * 60)
    print("\n【摘要】\n")
    print(f'{summary}')
        
    # except Exception as e:
    #     # 捕获并输出任何异常
    #     print(f"错误：处理音频时发生异常: {e}")
    #     # 如需调试完整堆栈信息，可取消注释下一行
    #     # import traceback; traceback.print_exc()
    return summary


def example_key_points_extraction(agent, config):
    """示例：提取关键要点"""
    audio_file = config.AGENT_CONFIG.get("audio_input")
    print(f"Using audio file: {audio_file}")
    print('开始提取关键要点...')
    try:
        key_points = agent.extract_key_points(audio_file)
        
        print("=" * 60)
        print("关键要点提取")
        print("=" * 60)
        for i, point in enumerate(key_points, 1):
            print(f"{i}. {point}")
            
    except FileNotFoundError:
        print(f"错误：找不到音频文件 {audio_file}")
    
    return key_points

def example_technical_terms_explanation(agent, config):
    """示例：解释技术术语"""
    audio_file = config.AGENT_CONFIG.get("audio_input")
    print(f"Using audio file: {audio_file}")
    print('开始解释专有名词...')
    try:
        terms = agent.explain_technical_terms(audio_file)
        print("=" * 60)
        print("专有名词解释")
        print("=" * 60)
        for i, term in enumerate(terms, 1):
            print(f"{i}. {term}")
            
    except FileNotFoundError:
        print(f"错误：找不到音频文件 {audio_file}")

    return terms

if __name__ == "__main__":
    # 运行示例
    # 加载配置
    load_dotenv()
    config = Config()
    # 生成智能体
    agent = TranscriptionAgent(
        agent_setting = config.AGENT_CONFIG,
        minutes_generator_setting= config.DEEPSEEK_SETTINGS
    )

    # 记录结果字典
    results = {}
    if config.USAGE_CONFIG.get("enable_meeting_transcription"):
        results['transcript'] = example_meeting_transcription(agent, config)

    # if config.USAGE_CONFIG.get("enable_meeting_summary_generation"):
    #     results['summary'] = example_meeting_summary_generation(agent, config)
    
    # if config.USAGE_CONFIG.get("enable_key_points_extraction"):
    #     results['key_point'] = example_key_points_extraction(agent, config)

    # if config.USAGE_CONFIG.get("enable_technical_terms_explanation"):
    #     results['technical_terms'] = example_technical_terms_explanation(agent, config)

    # agent.save_results(results, output_path=config.AGENT_CONFIG['output_dir'])
