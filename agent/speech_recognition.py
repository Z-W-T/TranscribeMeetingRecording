"""
语音识别模块
支持多种语音识别引擎：Whisper API、本地Whisper等
"""
import os
from typing import Optional, BinaryIO
from pathlib import Path


class SpeechRecognitionEngine:
    """语音识别引擎基类"""
    
    def transcribe(self, audio_input) -> str:
        """
        将语音转换为文字
        
        Args:
            audio_input: 音频文件路径或文件对象
            
        Returns:
            str: 转换后的文字
        """
        raise NotImplementedError


class WhisperAPIEngine(SpeechRecognitionEngine):
    """使用OpenAI Whisper API进行语音识别"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "whisper-1"):
        """
        初始化Whisper API引擎
        
        Args:
            api_key: OpenAI API密钥
            model: 使用的模型，默认为whisper-1
        """
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
            self.model = model
        except ImportError:
            raise ImportError("请安装openai库: pip install openai")
    
    def transcribe(self, audio_input) -> str:
        """
        使用Whisper API转换语音
        
        Args:
            audio_input: 音频文件路径或文件对象
            
        Returns:
            str: 转换后的文字
        """
        if isinstance(audio_input, str):
            audio_file = open(audio_input, "rb")
        else:
            audio_file = audio_input
        
        try:
            transcript = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                response_format="text"
            )
            return transcript
        finally:
            if isinstance(audio_input, str):
                audio_file.close()


class LocalWhisperEngine(SpeechRecognitionEngine):
    """使用本地Whisper模型进行语音识别"""
    
    def __init__(self, model_name: str = "base"):
        """
        初始化本地Whisper引擎
        
        Args:
            model_name: Whisper模型名称 (tiny, base, small, medium, large)
        """
        try:
            import whisper
            self.model = whisper.load_model(model_name)
        except ImportError:
            raise ImportError("请安装whisper库: pip install openai-whisper")
    
    def transcribe(self, audio_input) -> str:
        """
        使用本地Whisper转换语音
        
        Args:
            audio_input: 音频文件路径
            
        Returns:
            str: 转换后的文字
        """
        if isinstance(audio_input, str):
            audio_path = audio_input
        else:
            raise ValueError("LocalWhisperEngine只支持文件路径")
        
        result = self.model.transcribe(audio_path, language="zh")
        return result["text"]


def create_speech_engine(engine_type: str = "whisper_api", **kwargs) -> SpeechRecognitionEngine:
    """
    创建语音识别引擎
    
    Args:
        engine_type: 引擎类型 ("whisper_api", "local_whisper")
        **kwargs: 引擎参数
        
    Returns:
        SpeechRecognitionEngine: 语音识别引擎实例
    """
    if engine_type == "whisper_api":
        return WhisperAPIEngine(**kwargs)
    elif engine_type == "local_whisper":
        return LocalWhisperEngine(**kwargs)
    else:
        raise ValueError(f"不支持的引擎类型: {engine_type}")

