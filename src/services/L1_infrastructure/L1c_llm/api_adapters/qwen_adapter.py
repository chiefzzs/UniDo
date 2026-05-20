from typing import Dict, Any, List
from .base_adapter import BaseAdapter


class QwenAdapter(BaseAdapter):
    def build_request_payload(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        payload = {
            "model": self.model_name,
            "input": {"messages": messages},
            "parameters": {
                "temperature": kwargs.get('temperature', 0.7),
                "max_tokens": kwargs.get('max_tokens', 2048),
                "top_p": kwargs.get('top_p', 0.8),
            }
        }

        if kwargs.get('stream'):
            payload["parameters"]["incremental_output"] = True

        if kwargs.get('tools'):
            payload["parameters"]["tools"] = kwargs['tools']

        return payload

    def parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        output = response_data.get('output', {})
        choices = output.get('choices', [])

        if choices:
            choice = choices[0]
            return {
                'content': choice.get('message', {}).get('content', ''),
                'finish_reason': choice.get('finish_reason', 'stop'),
                'model_name': self.model_name,
                'usage': output.get('usage', {}),
                'tool_calls': choice.get('message', {}).get('tool_calls', [])
            }

        return {
            'content': '',
            'finish_reason': 'stop',
            'model_name': self.model_name,
            'usage': output.get('usage', {}),
            'tool_calls': []
        }

    def parse_stream_chunk(self, chunk_data: Dict[str, Any]) -> Dict[str, Any]:
        output = chunk_data.get('output', {})
        choices = output.get('choices', [])

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
        return f"{self.api_address}/services/aigc/text-generation/generation"
