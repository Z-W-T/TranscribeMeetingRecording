"""
会议纪要和摘要生成模块
"""
from typing import Dict, List, Optional
from datetime import datetime
from utils.api_client import call_deepseek_api
from config.prompts_manager import PromptManager

class MeetingMinutesGenerator:
    """会议纪要生成器"""
    
    def __init__(self, api_settings: Dict):
        """
        初始化会议纪要生成器
        
        Args:
            api_settings: API配置，包含api_key和model
        """
        self.api_settings = api_settings
    
    def generate_summary(self, transcript: str, additional_context: Optional[str] = None) -> str:
        """
        生成会议摘要
        
        Args:
            transcript: 会议转录文本
            additional_context: 额外的上下文信息
            
        Returns:
            str: 会议摘要
        """
        prompt = self._build_summary_prompt(transcript, additional_context)
        summary = call_deepseek_api(prompt, self.api_settings)
        return summary
    
    def generate_detailed_minutes(
        self, 
        transcript: str, 
        attendees: Optional[List[str]] = None,
        meeting_topic: Optional[str] = None
    ) -> Dict:
        """
        生成详细会议纪要
        
        Args:
            transcript: 会议转录文本
            attendees: 参会人员列表
            meeting_topic: 会议主题
            
        Returns:
            Dict: 包含详细会议纪要的字典
        """
        prompt = self._build_minutes_prompt(transcript, attendees, meeting_topic)
        minutes_text = call_deepseek_api(prompt, self.api_settings)
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "topic": meeting_topic or "未指定",
            "attendees": attendees or [],
            "summary": minutes_text,
            "transcript": transcript
        }
    
    def _build_summary_prompt(self, transcript: str, context: Optional[str] = None) -> str:
        """构建摘要生成prompt"""
        prompt_manager = PromptManager(config_path="config/prompts.yaml")
        prompt_manager._load_prompts()
        prompt = prompt_manager.get_prompt(prompt_key='meeting_summary', transcript=transcript, context=context)
        return prompt
        # prompt = f"""请为以下会议录音转录内容生成一个简洁的会议摘要。

        # 会议转录内容：
        # {transcript}
        # """
        # if context:
        #     prompt += f"\n额外背景信息：{context}"
        
        # prompt += "\n\n请生成一个结构化的会议摘要，包括主要讨论点、关键决策和待办事项。"
        # return prompt
    
    def _build_minutes_prompt(
        self, 
        transcript: str, 
        attendees: Optional[List[str]] = '未记录',
        topic: Optional[str] = '待定'
    ) -> str:
        """构建详细会议纪要prompt"""
        prompt_manager = PromptManager(config_path="config/prompts.yaml")
        prompt_manager._load_prompts()
        prompt = prompt_manager.get_prompt(prompt_key='meeting_minutes', meeting_topic=topic, attendees=attendees, transcript=transcript)
        return prompt
        # prompt = f"""请为以下会议录音内容生成详细的会议纪要。

        # 会议主题：{topic or '待定'}
        # 参会人员：{', '.join(attendees) if attendees else '未记录'}

        # 会议录音转录内容：
        # {transcript}

        # 请生成包含以下结构的详细会议纪要：
        # 1. 会议基本信息（主题、时间、参会人员）
        # 2. 主要讨论议题
        # 3. 关键决策和结论
        # 4. 行动项和责任人员
        # 5. 下次会议安排
        # 6. 备注事项
        # """
        # return prompt
    
    def extract_key_points(self, transcript: str) -> List[str]:
        """
        提取关键要点
        
        Args:
            transcript: 会议转录文本
            
        Returns:
            List[str]: 关键要点列表
        """
        promt_manager = PromptManager(config_path="config/prompts.yaml")
        promt_manager._load_prompts()
        prompt = promt_manager.get_prompt(prompt_key='meeting_key_points', transcript=transcript)
        # prompt = f"""请从以下会议录音转录中提取关键要点，每条要点以"-"开头。

        # 会议转录内容：
        # {transcript}

        # 请提取5-10个关键要点："""
        
        result = call_deepseek_api(prompt, self.api_settings)
        # 解析要点
        key_points = [line.strip()[1:].strip() for line in result.split("\n") if line.strip().startswith("-")]
        return key_points or [result]

