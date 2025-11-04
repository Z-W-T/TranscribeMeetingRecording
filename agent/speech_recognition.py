"""
语音识别模块
支持多种语音识别引擎：Whisper API、本地Whisper等
"""
import os
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
        # provider can be 'whisper' (default) or 'ifasr'
        self.provider = os.getenv('ASR_PROVIDER', 'whisper').lower()
        # IFASR credentials (if used)
        self.ifasr_appid = os.getenv('IFASR_APPID')
        self.ifasr_access_key_id = os.getenv('IFASR_ACCESS_KEY_ID')
        self.ifasr_access_key_secret = os.getenv('IFASR_ACCESS_KEY_SECRET')
        
    def transcribe(self, audio_input_path) -> str:
        """
        将语音转换为文字
        
        Args:
            audio_input_path: 音频文件路径或文件对象
            
        Returns:
            str: 转换后的文字
        """
        if self.provider == 'ifasr':
            # lazy import to avoid adding extra dependency unless requested
            try:
                from utils.ifasr_client import IfasrAPI
            except Exception as e:
                raise RuntimeError(f"IFASR provider selected but failed to import IfasrAPI: {e}") from e

            if not (self.ifasr_appid and self.ifasr_access_key_id and self.ifasr_access_key_secret):
                raise RuntimeError('IFASR provider selected but IFASR_APPID/IFASR_ACCESS_KEY_ID/IFASR_ACCESS_KEY_SECRET are not set in environment')

            ifasr = IfasrAPI(appid=self.ifasr_appid, access_key_id=self.ifasr_access_key_id, access_key_secret=self.ifasr_access_key_secret)
            transcript = ifasr.transcribe_audio(audio_input_path)
        else:
            whisper_api = WhisperAPI(api_key=self.api_key, model=self.model)
            transcript = whisper_api.transcribe_audio(audio_input_path)
        # with open('data/output/transcript.txt', 'r', encoding='utf-8') as f:
        #     transcript = f.read()
        return transcript


