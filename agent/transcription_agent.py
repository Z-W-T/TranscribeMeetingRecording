"""
智能转录和会议纪要生成智能体
整合语音识别和会议纪要生成功能
"""
import os
from typing import Optional, Dict, BinaryIO, List
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
        """
        self.speech_engine =SpeechRecognitionEngine(api_key=agent_setting.get("api_key"),
                                                    model=agent_setting.get("whisper_model"))
        self.minutes_generator = MeetingMinutesGenerator(
            api_settings=minutes_generator_setting
        )
    
    def transcribe_audio(self, audio_input, language: str = "zh") -> str:
        """
        将音频文件转换为文字
        
        Args:
            audio_input: 音频文件路径或文件对象
            language: 音频语言
            
        Returns:
            str: 转录文字
        """
        return self.speech_engine.transcribe(audio_input)
    
    def process_meeting(
        self,
        audio_input,
        generate_minutes: bool = True,
        generate_summary: bool = True,
        attendees: Optional[List[str]] = None,
        meeting_topic: Optional[str] = None
    ) -> Dict:
        """
        处理会议音频，生成转录和纪要
        
        Args:
            audio_input: 音频文件路径或文件对象
            generate_minutes: 是否生成详细纪要
            generate_summary: 是否生成摘要
            attendees: 参会人员列表
            meeting_topic: 会议主题
            
        Returns:
            Dict: 包含转录、摘要和详细纪要的字典
        """
        # 1. 转录语音
        transcript = self.transcribe_audio(audio_input)
        # transcript_path = os.getenv("TRANSCRIBED_TEXT_PATH")
        # with open(transcript_path, "r", encoding="utf-8") as f:
        #     transcript = f.read()
        result = {
            "transcript": transcript
        }
        
        # 2. 生成摘要（如果需要）
        if generate_summary:
            summary = self.minutes_generator.generate_summary(transcript)
            result["summary"] = summary
        
        # 3. 生成详细纪要（如果需要）
        if generate_minutes:
            minutes = self.minutes_generator.generate_detailed_minutes(
                transcript=transcript,
                attendees=attendees,
                meeting_topic=meeting_topic
            )
            result.update(minutes)
        
        return result
    
    def extract_key_points(self, audio_input) -> List[str]:
        """
        从音频中提取关键要点
        
        Args:
            audio_input: 音频文件路径或文件对象
            
        Returns:
            List[str]: 关键要点列表
        """
        transcript = self.transcribe_audio(audio_input)
        return self.minutes_generator.extract_key_points(transcript)
    
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
            transcript_file = output_dir / "transcript.txt"
            transcript_file.write_text(results["transcript"], encoding="utf-8")
        
        # 保存摘要
        if "summary" in results:
            summary_file = output_dir / "summary.txt"
            summary_file.write_text(results["summary"], encoding="utf-8")
        
        # 保存完整纪要
        if "date" in results:  # 如果生成的是详细纪要
            minutes_file = output_dir / "meeting_minutes.md"
            content = f"""# 会议纪要

**日期**: {results.get('date', 'N/A')}
**主题**: {results.get('topic', 'N/A')}
**参会人员**: {', '.join(results.get('attendees', []))}

## 摘要

{results.get('summary', '')}

## 完整转录

{results.get('transcript', '')}
"""
            minutes_file.write_text(content, encoding="utf-8")

