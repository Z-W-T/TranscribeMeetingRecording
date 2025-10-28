from dotenv import load_dotenv
from config.settings import Config
from openai import OpenAI
# API key is read automatically from the OPENAI_API_KEY env var
load_dotenv()
config = Config()
client = OpenAI(api_key=config.OPENAI_SETTINGS["api_key"])
try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", # 或其他可用模型，如 gpt-3.5-turbo
        messages=[
 {"role": "system", "content": "You are a helpful assistant."},
 {"role": "user", "content": "What is an OpenAI API Key?"}
 ]
 )
    print("Model Response:")
    print(response.choices[0].message.content)
 # 显示如何检查使用情况
    if response.usage:
        print(f"\nTokens used: {response.usage.total_tokens} (Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens})")
except Exception as e:
    print(f"An error occurred: {e}")