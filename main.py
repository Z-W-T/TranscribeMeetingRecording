from dotenv import load_dotenv
from config.settings import Config
from config.prompts_manager import PromptManager
from utils.api_client import call_deepseek_api

# 示例调用
if __name__ == "__main__":
    load_dotenv()
    config = Config()
    prompt_manager = PromptManager(config_path="config/prompts.yaml")
    prompt = prompt_manager.get_prompt(prompt_key="customer_service", question="什么是量子计算？", company_info="我们是一家专注于量子计算的公司", history="用户之前询问了关于量子计算的基本原理")
    result = call_deepseek_api(prompt, config.DEEPSEEK_SETTINGS)
    print(result)