import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 大型模型问答API配置
    DEEPSEEK_SETTINGS = {
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "model": os.getenv("DEEPSEEK_MODEL", "Qwen/QwQ-32B")  # 默认值
    }
    
    # 智能体配置
    AGENT_CONFIG = {
        "whisper_model": os.getenv("WHISPER_MODEL", "whisper-1"),
        "output_dir": os.getenv("OUTPUT_DIR", "data/output"),
        # 默认的音频输入路径，可通过环境变量 AUDIO_INPUT 覆盖，或在运行时修改 Config().AGENT_CONFIG
        "audio_input": os.getenv("AUDIO_INPUT", "data/dialogue_recording.mp3"),
        "api_key": os.getenv("OPENAI_API_KEY")
    }
    # ASR provider settings: allows switching between 'whisper' and 'ifasr'
    AGENT_CONFIG.update({
        "asr_provider": os.getenv("ASR_PROVIDER", "whisper"),
        "ifasr_appid": os.getenv("IFASR_APPID"),
        "ifasr_access_key_id": os.getenv("IFASR_ACCESS_KEY_ID"),
        "ifasr_access_key_secret": os.getenv("IFASR_ACCESS_KEY_SECRET"),
    })

    # 功能配置
    USAGE_CONFIG = {
        "enable_meeting_transcription": True,
        "enable_meeting_summary_generation": False,
        "enable_key_points_extraction": False,
        "enable_technical_terms_explanation": False
    }
    
    # @property
    # def pinecone_config(self):
    #     try:
    #         return {
    #             "api_key": os.environ["PINECONE_API_KEY"],
    #             "environment": os.environ["PINECONE_ENV"]
    #         }
    #     except KeyError as e:
    #         raise EnvironmentError(
    #             f"缺少Pinecone配置: {e.args[0]}"
    #         ) from None