from typing import Dict, Any, List, Optional


class ResponseParser:
    @staticmethod
    def parse(response_data: Dict[str, Any], api_type: str) -> Dict[str, Any]:
        if api_type == 'qwen':
            return ResponseParser._parse_qwen(response_data)
        elif api_type == 'openai':
            return ResponseParser._parse_openai(response_data)
        elif api_type == 'anthropic':
            return ResponseParser._parse_anthropic(response_data)
        else:
            return ResponseParser._parse_openai(response_data)

    @staticmethod
    def _parse_qwen(response_data: Dict[str, Any]) -> Dict[str, Any]:
        output = response_data.get('output', {})
        choices = output.get('choices', [])

        if choices:
            choice = choices[0]
            message = choice.get('message', {})
            return {
                'content': message.get('content', ''),
                'finish_reason': choice.get('finish_reason', 'stop'),
                'model_name': output.get('model', ''),
                'usage': output.get('usage', {}),
                'tool_calls': message.get('tool_calls', [])
            }
        return {'content': '', 'finish_reason': 'stop', 'model_name': '', 'usage': {}, 'tool_calls': []}

    @staticmethod
    def _parse_openai(response_data: Dict[str, Any]) -> Dict[str, Any]:
        choices = response_data.get('choices', [])
        if choices:
            choice = choices[0]
            message = choice.get('message', {})
            # 提取思考内容（可能在 message 或 choice 中）
            thinking = message.get('thinking', '') or message.get('reasoning', '') or choice.get('thinking', '') or choice.get('reasoning', '')
            return {
                'content': message.get('content', ''),
                'thinking': thinking,
                'finish_reason': choice.get('finish_reason', 'stop'),
                'model_name': response_data.get('model', ''),
                'usage': response_data.get('usage', {}),
                'tool_calls': message.get('tool_calls', [])
            }
        return {'content': '', 'thinking': '', 'finish_reason': 'stop', 'model_name': '', 'usage': {}, 'tool_calls': []}

    @staticmethod
    def _parse_anthropic(response_data: Dict[str, Any]) -> Dict[str, Any]:
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
            'model_name': response_data.get('model', ''),
            'usage': response_data.get('usage', {}),
            'tool_calls': tool_calls
        }

    @staticmethod
    def parse_stream_chunk(chunk_line: str, api_type: str) -> Optional[Dict[str, Any]]:
        import json
        try:
            chunk_data = json.loads(chunk_line)
        except json.JSONDecodeError:
            return None

        if api_type == 'qwen':
            return ResponseParser._parse_qwen_stream(chunk_data)
        elif api_type == 'openai':
            return ResponseParser._parse_openai_stream(chunk_data)
        elif api_type == 'anthropic':
            return ResponseParser._parse_anthropic_stream(chunk_data)
        return None

    @staticmethod
    def _parse_qwen_stream(chunk_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
        return None

    @staticmethod
    def _parse_openai_stream(chunk_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if chunk_data.get('choices'):
            choice = chunk_data['choices'][0]
            delta = choice.get('delta', {})
            return {
                'delta': delta.get('content', ''),
                'chunk_type': 'text',
                'finish_reason': choice.get('finish_reason'),
                'index': choice.get('index', 0),
                'tool_calls': delta.get('tool_calls', [])
            }
        return None

    @staticmethod
    def _parse_anthropic_stream(chunk_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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

        return None
