from typing import Dict, Any, List
from .base_adapter import BaseAdapter


class AnthropicAdapter(BaseAdapter):
    def build_request_payload(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        anthropic_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                anthropic_messages.append({"role": "user", "content": f"System: {msg['content']}"})
            else:
                anthropic_messages.append(msg)

        payload = {
            "model": self.model_name,
            "messages": anthropic_messages,
            "temperature": kwargs.get('temperature', 0.7),
            "max_tokens": kwargs.get('max_tokens', 2048),
        }

        if kwargs.get('stream'):
            payload["stream"] = True

        system_prompt = kwargs.get('system_prompt')
        if system_prompt:
            payload["system"] = system_prompt

        if kwargs.get('tools'):
            payload["tools"] = kwargs['tools']

        return payload

    def parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        content = response_data.get('content', [])

        text_content = ''
        tool_calls = []
        if content:
            for block in content:
                if block.get('type') == 'text':
                    text_content = block.get('text', '')
                elif block.get('type') == 'tool_use':
                    tool_calls.append({
                        'id': block.get('id', ''),
                        'name': block.get('name', ''),
                        'input': block.get('input', {})
                    })

        return {
            'content': text_content,
            'finish_reason': response_data.get('stop_reason', 'stop'),
            'model_name': self.model_name,
            'usage': response_data.get('usage', {}),
            'tool_calls': tool_calls
        }

    def parse_stream_chunk(self, chunk_data: Dict[str, Any]) -> Dict[str, Any]:
        chunk_type = chunk_data.get('type', '')

        if chunk_type == 'content_block_delta':
            delta = chunk_data.get('delta', {})
            if delta.get('type') == 'text_delta':
                return {
                    'delta': delta.get('text', ''),
                    'chunk_type': 'text',
                    'finish_reason': None,
                    'index': chunk_data.get('index', 0),
                    'tool_calls': []
                }
            elif delta.get('type') == 'tool_use_delta':
                return {
                    'delta': '',
                    'chunk_type': 'tool_call',
                    'finish_reason': None,
                    'index': chunk_data.get('index', 0),
                    'tool_calls': [{
                        'id': chunk_data.get('id', ''),
                        'name': chunk_data.get('name', ''),
                        'input_delta': delta.get('input', '')
                    }]
                }

        elif chunk_type == 'message_delta':
            return {
                'delta': '',
                'chunk_type': 'text',
                'finish_reason': chunk_data.get('delta', {}).get('stop_reason'),
                'index': 0,
                'tool_calls': []
            }

        return {
            'delta': '',
            'chunk_type': 'text',
            'finish_reason': None,
            'index': 0,
            'tool_calls': []
        }

    def get_api_endpoint(self) -> str:
        return f"{self.api_address}/v1/messages"
