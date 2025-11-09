from dotenv import load_dotenv
from config.settings import Config
from agent.transcription_agent import TranscriptionAgent

import os
import sys
import uvicorn
import asyncio
import threading
import webbrowser
from pathlib import Path

# 添加当前目录到 Python 路径，确保可以导入本地模块
sys.path.insert(0, str(Path(__file__).parent))

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
    print(f'{transcript}\n')

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

def resource_path(relative_path):
    """获取资源的绝对路径，用于打包后访问资源文件"""
    try:
        # PyInstaller 创建的临时文件夹
        base_path = sys._MEIPASS
    except Exception:
        # 开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)

def main():
    """应用主函数"""
    # 设置环境变量
    os.environ["PYTHONUNBUFFERED"] = "1"
    
    # 配置信息
    host = "127.0.0.1"
    port = 8001
    app_module = "api_server"  # 您的 FastAPI 应用模块名
    app_variable = "app"      # FastAPI 应用实例变量名
    
    print("=" * 50)
    print("FastAPI 应用启动器")
    print("=" * 50)
    
    # 检查是否是打包版本
    if getattr(sys, 'frozen', False):
        print("✅ 运行在打包环境中")
        # 设置资源路径
        static_dir = resource_path('static')
        frontend_dir = resource_path('frontend')
    else:
        print("🔧 运行在开发环境中")
        static_dir = os.path.join(os.path.dirname(__file__), 'static')
        frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    
    print(f"静态文件目录: {static_dir}")
    print(f"前端目录: {frontend_dir}")
    
    # 启动信息
    url = f"http://{host}:{port}"
    print(f"🚀 启动服务器: {url}")
    print("⏹️  按 Ctrl+C 停止服务器")
    print("-" * 50)
    
    # 在浏览器中打开应用（可选）
    def open_browser():
        import time
        time.sleep(2)  # 等待服务器启动
        try:
            webbrowser.open(url)
            print(f"🌐 在浏览器中打开: {url}")
        except Exception as e:
            print(f"❌ 无法打开浏览器: {e}")
    
    # 在后台线程中打开浏览器
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # 配置并启动 uvicorn 服务器
    config = uvicorn.Config(
        app=f"{app_module}:{app_variable}",
        host=host,
        port=port,
        log_level="info",
        access_log=True,
        reload=False,  # 打包后禁用热重载
    )
    
    server = uvicorn.Server(config)
    
    try:
        # 启动服务器
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # 运行示例
    # 加载配置
    # load_dotenv()
    # config = Config()
    # # 生成智能体
    # agent = TranscriptionAgent(
    #     agent_setting = config.AGENT_CONFIG,
    #     minutes_generator_setting= config.DEEPSEEK_SETTINGS
    # )

    # 记录结果字典
    # results = {}
    # if config.USAGE_CONFIG.get("enable_meeting_transcription"):
    #     results['transcript'] = example_meeting_transcription(agent, config)

    # if config.USAGE_CONFIG.get("enable_meeting_summary_generation"):
    #     results['summary'] = example_meeting_summary_generation(agent, config)
    
    # if config.USAGE_CONFIG.get("enable_key_points_extraction"):
    #     results['key_point'] = example_key_points_extraction(agent, config)

    # if config.USAGE_CONFIG.get("enable_technical_terms_explanation"):
    #     results['technical_terms'] = example_technical_terms_explanation(agent, config)

    # agent.save_results(results, output_path=config.AGENT_CONFIG['output_dir'])

    main()
