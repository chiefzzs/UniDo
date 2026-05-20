from typing import List, Dict, Any, Optional
from .llm_client import LLMRequest


class RequestConstructor:
    def __init__(self, model_config: Dict[str, Any]):
        self.model_config = model_config

    def build(self, messages: List[Dict[str, str]], **kwargs) -> LLMRequest:
        model_name = kwargs.get('model_name') or self.model_config.get('model_name', 'demo')
        api_type = kwargs.get('api_type') or self.model_config.get('api_type', 'openai')
        api_address = kwargs.get('api_address') or self.model_config.get('api_address', 'http://localhost/v1')
        api_key = kwargs.get('api_key') or self.model_config.get('api_key', 'demo')

        temperature = kwargs.get('temperature') if 'temperature' in kwargs else self.model_config.get('temperature', 0.7)
        max_tokens = kwargs.get('max_tokens') if 'max_tokens' in kwargs else self.model_config.get('max_tokens', 2048)
        stream = kwargs.get('stream', False)
        tools = kwargs.get('tools')
        tool_choice = kwargs.get('tool_choice')

        return LLMRequest(
            model_name=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            api_type=api_type,
            api_address=api_address,
            api_key=api_key,
            tools=tools,
            tool_choice=tool_choice
        )
