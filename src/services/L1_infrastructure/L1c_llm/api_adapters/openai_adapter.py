from typing import Dict, Any, List
from .base_adapter import BaseAdapter


class OpenAIAdapter(BaseAdapter):
    def build_request_payload(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": kwargs.get('temperature', 0.7),
            "max_tokens": kwargs.get('max_tokens', 2048),
        }

        if kwargs.get('stream'):
            payload["stream"] = True

        if kwargs.get('tools'):
            payload["tools"] = kwargs['tools']
            if kwargs.get('tool_choice'):
                payload["tool_choice"] = kwargs['tool_choice']

        return payload

    def parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        choices = response_data.get('choices', [])

        if choices:
            choice = choices[0]
            message = choice.get('message', {})
            return {
                'content': message.get('content', ''),
                'finish_reason': choice.get('finish_reason', 'stop'),
                'model_name': response_data.get('model', self.model_name),
                'usage': response_data.get('usage', {}),
                'tool_calls': message.get('tool_calls', [])
            }

        return {
            'content': '',
            'finish_reason': 'stop',
            'model_name': self.model_name,
            'usage': {},
            'tool_calls': []
        }

    def parse_stream_chunk(self, chunk_data: Dict[str, Any]) -> Dict[str, Any]:
        choices = chunk_data.get('choices', [])

        if choices:
            choice = choices[0]
            delta = choice.get('delta', {})
            return {
                'delta': delta.get('content', ''),
                'chunk_type': 'text',
                'finish_reason': choice.get('finish_reason'),
                'index': choice.get('index', 0),
                'tool_calls': delta.get('tool_calls', [])
            }

        return {
            'delta': '',
            'chunk_type': 'text',
            'finish_reason': None,
            'index': 0,
            'tool_calls': []
        }

    def get_api_endpoint(self) -> str:
        address = self.api_address.rstrip('/')
        if address.endswith('/v1'):
            return f"{address}/chat/completions"
        return f"{address}/v1/chat/completions"
