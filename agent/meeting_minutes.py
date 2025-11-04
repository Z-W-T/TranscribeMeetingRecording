"""
会议纪要和摘要生成模块
"""
from typing import Dict, List, Optional
from datetime import datetime
from utils.api_client import DeepseekAPI
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
        # Instantiate DeepseekAPI client for making LLM calls
        api_key = None
        model = None
        try:
            api_key = api_settings.get("api_key")
            model = api_settings.get("model")
        except Exception:
            # api_settings may be None or not a dict
            api_key = None
            model = None

        if api_key:
            self.client = DeepseekAPI(api_key=api_key, model=model or "gpt-3.5-turbo")
        else:
            # Lazy: set client to None and let calls fail clearly if no API key provided
            self.client = None
    
    def generate_transcript(self, tanscript_str) -> str:
        """
        将拼接文本转为正常脚本
        
        Args:
            tanscript_str: 拼接字符串
            
        Returns:
            str: 对话脚本
        """
        prompt = self._build_transcript_prompt(tanscript_str)
        if not self.client:
            raise RuntimeError("Deepseek API client not configured (missing api_key in api_settings)")
        transcript = self.client.call_api(prompt)
        return transcript 

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
        if not self.client:
            raise RuntimeError("Deepseek API client not configured (missing api_key in api_settings)")
        summary = self.client.call_api(prompt)
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
        if not self.client:
            raise RuntimeError("Deepseek API client not configured (missing api_key in api_settings)")
        minutes_text = self.client.call_api(prompt)
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "topic": meeting_topic or "未指定",
            "attendees": attendees or [],
            "summary": minutes_text,
            "transcript": transcript
        }
    
    def _build_transcript_prompt(self, tanscript_str) -> str:
        """构建对话脚本提取prompt"""
        prompt_manager = PromptManager(config_path="config/prompts.yaml")
        prompt = prompt_manager.get_prompt(prompt_key='transcript_extraction',transcript = tanscript_str)
        return prompt

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
    
    def _build_key_points_prompt(self, transcript: str) -> str:
        """构建关键要点提取prompt"""
        prompt_manager = PromptManager(config_path="config/prompts.yaml")
        prompt_manager._load_prompts()
        prompt = prompt_manager.get_prompt(prompt_key='meeting_key_points', transcript=transcript)
        return prompt
        # prompt = f"""请从以下会议录音转录中提取关键要点，每条要点以"-"开头。

        # 会议转录内容：
        # {transcript}

        # 请提取5-10个关键要点："""

    def extract_key_points(self, transcript: str) -> List[str]:
        """
        提取关键要点
        
        Args:
            transcript: 会议转录文本
            
        Returns:
            List[str]: 关键要点列表
        """
        prompt = self._build_key_points_prompt(transcript)
        if not self.client:
            raise RuntimeError("Deepseek API client not configured (missing api_key in api_settings)")
        result = self.client.call_api(prompt)
        # 解析要点
        key_points = [line.strip()[1:].strip() for line in result.split("\n") if line.strip().startswith("-")]
        return key_points or [result]
    
    def _build_technical_terms_explanation_prompt(self, transcript: str) -> str:
        """构建专有名词解释prompt"""
        prompt_manager = PromptManager(config_path="config/prompts.yaml")
        prompt_manager._load_prompts()
        prompt = prompt_manager.get_prompt(prompt_key='meeting_technical_term_explanation', transcript=transcript)
        return prompt
        # prompt = f"""请从以下会议录音转录中识别并解释所有专有名词。

        # 会议转录内容：
        # {transcript}

        # 请列出每个专有名词及其简要解释："""
    
    def explain_technical_terms(self, transcript: str) -> list[str]:
        """
        解释技术术语
        
        Args:
            transcript: 会议转录文本
            
        Returns:
            Dict[str:str]: 术语解释列表
        """
        prompt = self._build_technical_terms_explanation_prompt(transcript)  
        
        if not self.client:
            raise RuntimeError("Deepseek API client not configured (missing api_key in api_settings)")
        result = self.client.call_api(prompt)
        # 解析术语解释
        terms = {line.strip()[1:].strip() for line in result.split("\n") if line.strip().startswith("-")} 
        return terms

        

