import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEEPSEEK_SETTINGS = {
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
        "model": os.getenv("DEEPSEEK_MODEL", "Qwen/QwQ-32B")  # 默认值
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