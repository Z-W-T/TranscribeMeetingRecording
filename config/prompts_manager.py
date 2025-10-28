import yaml
import os
from typing import Dict, Any, List

class PromptManager:
    def __init__(self, config_path: str = "prompts.yaml"):
        self.config_path = config_path
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict:
        """加载YAML配置文件"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get_prompt(self, prompt_key: str, **kwargs) -> str:
        """获取填充后的prompt"""
        if prompt_key not in self.prompts['prompts']:
            raise KeyError(f"Prompt '{prompt_key}' not found")
        
        prompt_config = self.prompts['prompts'][prompt_key]
        template = prompt_config['template']
        
        # 验证参数
        self._validate_parameters(prompt_key, kwargs, prompt_config.get('parameters', []))
        
        return template.format(**kwargs)
    
    def _validate_parameters(self, prompt_key: str, provided_params: Dict, expected_params: List[str]):
        """验证参数完整性"""
        missing_params = set(expected_params) - set(provided_params.keys())
        if missing_params:
            raise ValueError(f"Prompt '{prompt_key}' missing parameters: {missing_params}")