"""
智能转录和会议纪要生成智能体
整合语音识别和会议纪要生成功能
"""
import os
from typing import Optional, Dict, BinaryIO, List, Callable
from pathlib import Path
from agent.speech_recognition import SpeechRecognitionEngine
from agent.meeting_minutes import MeetingMinutesGenerator

class TranscriptionAgent:
    """智能转录代理"""
    
    def __init__(
        self,
        agent_setting: Dict,
        minutes_generator_setting: Dict
    ):
        """
        初始化智能转录代理
        
        Args:
            agent_setting: 智能体配置字典(包含模型名称，输入音频路径，api_key,输出路径)
            minutes_generator_setting: 会议纪要生成器配置字典(包含api_key,模型名称)
        """
        self.agent_setting = agent_setting
        self.speech_engine =SpeechRecognitionEngine(api_key=agent_setting.get("api_key"),
                                                    model=agent_setting.get("whisper_model"))
        self.minutes_generator = MeetingMinutesGenerator(
            api_settings=minutes_generator_setting
        )
        self.transcript: Optional[str] = None  # 缓存转录结果

    def transcribe_audio(self, audio_input, progress_callback: Optional[Callable[[int], None]] = None, language: str = "zh") -> str:
        """
        将音频文件转换为文字
        
        Args:
            audio_input: 音频文件路径或文件对象
            language: 音频语言
            
        Returns:
            str: 转录文字
        """
        # 如果已经转录过，直接返回缓存结果
        if self.transcript and self.audio_input == audio_input:
            return self.transcript
        self.audio_input = audio_input  # 缓存音频输入
        # with open(r'data/output/transcript.md', 'w', encoding='utf-8') as f:
        #     transcript = f.read()
        # 调用语音识别引擎进行转录
        transcript = self.speech_engine.transcribe(audio_input, progress_callback=progress_callback)

        # 生成对话格式
        transcript = self.minutes_generator.generate_transcript(transcript)
        progress_callback(100) if progress_callback else None
        self.transcript = transcript
        return self.transcript
    
    def generate_summary(
        self,
    ) -> str:
        """
        处理会议音频，生成转录和纪要
            
        Returns:
            str: 会议纪要
        """
        return self.minutes_generator.generate_summary(self.transcript)
        
    
    def extract_key_points(self) -> List[str]:
        """
        从音频中提取关键要点
            
        Returns:
            List[str]: 关键要点列表
        """
        return self.minutes_generator.extract_key_points(self.transcript)
    
    def explain_technical_terms(self) -> List[str]:
        """
        解释音频中的技术术语
        
        Args:
            audio_input: 音频文件路径或文件对象
            
        Returns:
            Dict[str, str]: 术语及其解释的字典
        """
        return self.minutes_generator.explain_technical_terms(self.transcript)
    
    def save_results(self, results: Dict, output_path: str = "output"):
        """
        保存处理结果到文件
        
        Args:
            results: 处理结果字典
            output_path: 输出目录路径
        """
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存转录文本
        if "transcript" in results:
            transcript_file = output_dir / "transcript.md"
            if not transcript_file.exists():
                transcript_file.touch()
            transcript_file.write_text(results["transcript"], encoding="utf-8")
        
        # 保存摘要
        if "summary" in results:
            summary_file = output_dir / "summary.md"
            if not summary_file.exists():
                summary_file.touch()
            summary_file.write_text(results["summary"], encoding="utf-8")

        # 保存关键要点
        if "key_points" in results:
            key_points_file = output_dir / "key_points.md"
            if not key_points_file.exists():
                key_points_file.touch()
            content = "\n".join([f"- {point}" for point in results["key_points"]])
            key_points_file.write_text(content, encoding="utf-8")

        # 保存专有名词解释
        if "technical_terms" in results:
            terms_file = output_dir / "technical_terms.md"
            if not terms_file.exists():
                terms_file.touch()
            content = "\n".join([f"- {term}" for term in results["technical_terms"]])
            terms_file.write_text(content, encoding="utf-8")
        
        print(f"Results saved to {output_dir.resolve()}")

