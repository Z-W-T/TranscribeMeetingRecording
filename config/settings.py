import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEEPSEEK_SETTINGS = {
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "model": os.getenv("DEEPSEEK_MODEL", "Qwen/QwQ-32B")  # 默认值
    }
    
    # OpenAI配置（用于Whisper语音识别）
    OPENAI_SETTINGS = {
        "api_key": os.getenv("OPENAI_API_KEY"),
    }
    
    # 智能体配置
    AGENT_CONFIG = {
        "speech_engine_type": os.getenv("SPEECH_ENGINE_TYPE", "whisper_api"),  # whisper_api 或 local_whisper
        "whisper_model": os.getenv("WHISPER_MODEL", "whisper-1"),
        "output_dir": os.getenv("OUTPUT_DIR", "data/output")
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