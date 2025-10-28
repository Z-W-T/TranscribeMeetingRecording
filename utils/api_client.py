import requests
import json


def build_request_data(prompt, settings):
    """构建API请求所需的数据体。"""
    return {
        "model": settings["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000
    }


def build_headers(settings):
    """构建API请求所需的headers。"""
    api_key = settings["api_key"]
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }


def send_api_request(url, headers, data):
    """发送POST请求到API并返回响应。"""
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    return response.json()


def parse_api_response(response_json):
    """从API响应中提取内容。"""
    return response_json["choices"][0]["message"]["content"]


def call_deepseek_api(prompt, settings):
    """对外暴露的主函数：调用API、返回模型应答。"""
    url = "https://api.siliconflow.cn/v1/chat/completions"
    headers = build_headers(settings)
    data = build_request_data(prompt, settings)
    response_json = send_api_request(url, headers, data)
    return parse_api_response(response_json)

