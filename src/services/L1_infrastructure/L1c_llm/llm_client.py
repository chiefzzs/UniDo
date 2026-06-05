import uuid
import time
import httpx
import os
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Optional

from .api_adapters import QwenAdapter, OpenAIAdapter, AnthropicAdapter, BaseAdapter
from .response_parser import ResponseParser


@dataclass
class LLMRequest:
    model_name: str
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: int = 2048
    stream: bool = False
    api_type: str = 'openai'
    api_address: str = 'http://localhost'
    api_key: str = 'demo'
    tools: List[Dict] = None
    tool_choice: str = None

    def __post_init__(self):
        if self.tools is None:
            self.tools = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            'model_name': self.model_name,
            'messages': self.messages,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'stream': self.stream,
            'api_type': self.api_type,
            'api_address': self.api_address,
            'api_key': self.api_key,
            'tools': self.tools,
            'tool_choice': self.tool_choice
        }


@dataclass
class LLMResponse:
    content: str
    finish_reason: str
    model_name: str
    thinking: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    tool_calls: List[Dict] = field(default_factory=list)


@dataclass
class StreamChunk:
    chunk_id: str
    delta: str
    chunk_type: str
    finish_reason: Optional[str] = None
    index: int = 0
    tool_calls: List[Dict] = field(default_factory=list)


class LLMClient:
    _instance: Optional['LLMClient'] = None

    def __init__(self, persistence_service=None):
        self._persistence_service = persistence_service
        self._adapters: Dict[str, BaseAdapter] = {}
        self._response_parser = ResponseParser()
        self._mode = 'record'  # 'record' or 'loopback'
    
    def set_mode(self, mode: str):
        """设置模式（record/loopback）"""
        self._mode = mode
        mode_display = "📹 录制模式" if mode == 'record' else "🔄 回放模式"
        print(f"🔄 LLMClient 模式切换: {mode_display}")

    def _get_adapter(self, api_type: str, api_address: str, api_key: str, model_name: str) -> BaseAdapter:
        key = f"{api_type}:{api_address}"
        if key not in self._adapters:
            if api_type == 'qwen':
                self._adapters[key] = QwenAdapter(api_address, api_key, model_name)
            elif api_type == 'anthropic':
                self._adapters[key] = AnthropicAdapter(api_address, api_key, model_name)
            else:
                self._adapters[key] = OpenAIAdapter(api_address, api_key, model_name)
        return self._adapters[key]

    def _build_headers(self, api_key: str, api_type: str) -> Dict[str, str]:
        if api_type == 'anthropic':
            return {
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            }
        return {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

    def _save_call_record(self, session_id: Optional[str], model_config_id: Optional[str],
                          request_data: Dict, response_data: Dict, status: str, duration_ms: int):
        # 回放模式下不保存调用记录
        if self._mode == 'loopback':
            print(f"🔄 [LLMClient] 回放模式跳过保存调用记录")
            return
            
        if self._persistence_service is None:
            return

        call_record = {
            'call_id': f"llm-{uuid.uuid4().hex[:12]}",
            'session_id': session_id,
            'model_config_id': model_config_id,
            'request': request_data,
            'response': response_data,
            'status': status,
            'duration_ms': duration_ms,
            'created_at': datetime.now().isoformat()
        }
        self._persistence_service.save('llm_calls', call_record)

    def send_request(self, request: LLMRequest, session_id: Optional[str] = None,
                    model_config_id: Optional[str] = None) -> LLMResponse:
        # 真实调用大模型
        start_time = time.time()
        adapter = self._get_adapter(request.api_type, request.api_address, request.api_key, request.model_name)

        request_payload = adapter.build_request_payload(
            request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=request.stream,
            tools=request.tools if request.tools else None,
            tool_choice=request.tool_choice
        )

        headers = self._build_headers(request.api_key, request.api_type)
        endpoint = adapter.get_api_endpoint()

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(endpoint, json=request_payload, headers=headers)
                response.raise_for_status()
                response_data = response.json()

            parsed = self._response_parser.parse(response_data, request.api_type)
            duration_ms = int((time.time() - start_time) * 1000)
            self._save_call_record(session_id, model_config_id, request_payload, response_data, 'completed', duration_ms)

            return LLMResponse(
                content=parsed.get('content', ''),
                thinking=parsed.get('thinking', ''),
                finish_reason=parsed.get('finish_reason', 'stop'),
                model_name=parsed.get('model_name', request.model_name),
                usage=parsed.get('usage', {}),
                tool_calls=parsed.get('tool_calls', [])
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self._save_call_record(session_id, model_config_id, request_payload, {'error': str(e)}, 'failed', duration_ms)
            raise

    def send_stream_request(self, request: LLMRequest, on_chunk: Callable[[StreamChunk], None],
                           session_id: Optional[str] = None, model_config_id: Optional[str] = None) -> LLMResponse:
        # 真实调用大模型
        start_time = time.time()
        adapter = self._get_adapter(request.api_type, request.api_address, request.api_key, request.model_name)

        request_payload = adapter.build_request_payload(
            request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True,
            tools=request.tools if request.tools else None,
            tool_choice=request.tool_choice
        )

        headers = self._build_headers(request.api_key, request.api_type)
        endpoint = adapter.get_api_endpoint()

        collected_content = []
        all_tool_calls = []
        final_finish_reason = None
        chunk_index = 0

        try:
            with httpx.Client(timeout=120.0) as client:
                with client.stream('POST', endpoint, json=request_payload, headers=headers) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line.startswith('data: '):
                            line = line[6:]
                        if line.strip() == '[DONE]' or line.strip() == '':
                            continue

                        chunk = self._response_parser.parse_stream_chunk(line, request.api_type)
                        if chunk:
                            chunk_index += 1
                            stream_chunk = StreamChunk(
                                chunk_id=f"chunk-{uuid.uuid4().hex[:8]}",
                                delta=chunk.get('delta', ''),
                                chunk_type=chunk.get('chunk_type', 'text'),
                                finish_reason=chunk.get('finish_reason'),
                                index=chunk.get('index', 0),
                                tool_calls=chunk.get('tool_calls', [])
                            )
                            collected_content.append(stream_chunk.delta)
                            if stream_chunk.tool_calls:
                                all_tool_calls.extend(stream_chunk.tool_calls)
                            if stream_chunk.finish_reason:
                                final_finish_reason = stream_chunk.finish_reason
                            on_chunk(stream_chunk)

            duration_ms = int((time.time() - start_time) * 1000)
            self._save_call_record(session_id, model_config_id, request_payload,
                                   {'content': ''.join(collected_content)}, 'completed', duration_ms)

            return LLMResponse(
                content=''.join(collected_content),
                finish_reason=final_finish_reason or 'stop',
                model_name=request.model_name,
                usage={},
                tool_calls=all_tool_calls
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self._save_call_record(session_id, model_config_id, request_payload, {'error': str(e)}, 'failed', duration_ms)
            raise

    @classmethod
    def get_instance(cls) -> 'LLMClient':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def set_persistence_service(cls, persistence_service):
        if cls._instance is None:
            cls._instance = cls(persistence_service)
        else:
            cls._instance._persistence_service = persistence_service


def get_llm_client() -> LLMClient:
    return LLMClient.get_instance()
