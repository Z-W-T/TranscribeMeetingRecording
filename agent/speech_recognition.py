"""
语音识别模块
支持多种语音识别引擎：Whisper API、本地Whisper等
"""
from utils.api_client import WhisperAPI

class SpeechRecognitionEngine:
    """语音识别引擎"""

    def __init__(self, api_key: str, model: str):
        """
        初始化语音识别引擎
        
        Args:
            api_key: API密钥
            model: 使用的模型名称
        """
        self.api_key = api_key
        self.model = model
        
    def transcribe(self, audio_input_path) -> str:
        """
        将语音转换为文字
        
        Args:
            audio_input_path: 音频文件路径或文件对象
            
        Returns:
            str: 转换后的文字
        """
        # whisper_api = WhisperAPI(api_key=self.api_key, model=self.model)
        # transcript = whisper_api.transcribe_audio(audio_input_path)
        with open('data/output/transcript.txt', 'r', encoding='utf-8') as f:
            transcript = f.read()
        return transcript


