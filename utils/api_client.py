import requests
import json

# 大模型问答
class DeepseekAPI():
    def __init__(self, api_key, model="gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.siliconflow.cn/v1"
        self.url = f"{self.base_url}/chat/completions"

    def build_request_data(self, prompt):
        """构建API请求所需的数据体。"""
        return {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "stream": True
        }

    def build_headers(self):
        """构建API请求所需的headers。"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def send_api_request(self, data):
        """发送POST请求到API并返回响应。"""
        headers = self.build_headers()
        response = requests.post(self.url, headers=headers, data=json.dumps(data))
        # 流式处理响应
        full_response = ""
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data: '):
                    try:
                        json_data = json.loads(decoded_line[6:])
                        if 'choices' in json_data and len(json_data['choices']) > 0:
                            delta = json_data['choices'][0].get('delta', {})
                            if 'content' in delta:
                                content = delta['content']
                                full_response += content
                                print(content, end='', flush=True)  # 实时显示
                    except json.JSONDecodeError:
                        continue
        response.raise_for_status()
        return full_response

    def parse_api_response(self, response_json):
        """从API响应中提取内容。"""
        return response_json["choices"][0]["message"]["content"]

    def call_api(self, prompt):
        """对外暴露的主函数：调用API、返回模型应答。"""
        data = self.build_request_data(prompt)
        response_json = self.send_api_request(data)
        return response_json
        # return self.parse_api_response(response_json)
    
# 语音转文字
class WhisperAPI():
    def __init__(self, api_key, model="whisper-1"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://work.poloapi.com/v1"
        self.url = f"{self.base_url}/audio/transcriptions"

    def build_headers(self):
        """构建API请求所需的headers。"""
        return {
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def build_data(self, audio_file_path):
        """构建API请求所需的数据体。"""
        # NOTE: keep file handling to the caller so that the file object
        # remains open while requests.post is executed. This helper returns
        # the meta parts; caller should open the file and include it in files.
        return {
            "model": (None, self.model),
            "response_format": (None, "text")
        }

    def transcribe_audio(self, audio_file_path):
        """发送音频文件到Whisper API并返回转录文本。"""
        headers = self.build_headers()
        # Open the file here and keep the file object alive for the duration
        # of the HTTP request. Previously the file was opened in a helper and
        # closed before requests.post ran which caused errors at runtime.
        extra = self.build_data(audio_file_path)
        with open(audio_file_path, "rb") as audio_file:
            files = {"file": audio_file, **extra}
            response = requests.post(self.url, headers=headers, files=files)
        response.raise_for_status()
        return response.text


