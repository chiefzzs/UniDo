"""
L2d LLM Execution Service

L2d LLM 执行服务负责执行 LLM 调用、处理流式响应、解析工具调用并协调工具执行。

职责：
- 执行 LLM 请求（从 L2e 获取构造好的请求）
- 处理流式响应
- 解析工具调用
- 管理 LLM 执行状态
- 生成对话响应

依赖 L1 层：
- L1c LLM 客户端：发送 LLM 请求
- L1b 持久化服务：存储 LLM 调用记录

依赖 L2 层：
- L2e 请求构造服务：获取构造好的请求（含工具/技能描述）
- L2b 记忆与状态管理：获取对话历史
- L2c 工具执行服务：执行工具调用
"""

import uuid
import time
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field, asdict

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.L1_infrastructure.L1b_persistence.storage_factory import StorageFactory
from services.L1_infrastructure.L1c_llm.llm_client import LLMClient, LLMRequest, LLMResponse
from services.L1_infrastructure.L1d_events.event_bus import EventBus, Event
from services.L1_infrastructure.L1d_events.event_types import EventTypes


@dataclass
class LLMExecutionRequest:
    dialog_id: str
    messages: List[Dict[str, str]]
    model_config_id: str
    stream: bool = False
    max_tokens: int = 2000
    temperature: float = 0.7

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMExecutionRequest':
        return cls(**data)


@dataclass
class LLMExecutionResponse:
    request_id: str
    dialog_id: str
    content: str
    finish_reason: str
    tool_calls: Optional[List[Dict]] = None
    usage: Dict[str, int] = field(default_factory=dict)
    status: str = "completed"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMExecutionResponse':
        return cls(**data)


@dataclass
class LLMCallRecord:
    call_id: str
    dialog_id: str
    model_config_id: str
    request: Dict[str, Any]
    response: Dict[str, Any]
    status: str = "completed"
    duration_ms: int = 0
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMCallRecord':
        return cls(**data)


@dataclass
class ToolCallContext:
    tool_call_id: str
    request_id: str
    dialog_id: str
    tool_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    result: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolCallContext':
        return cls(**data)


class LLMExecutionService:
    def __init__(self, persistence_service=None, llm_client: LLMClient = None,
                 event_bus=None):
        self.persistence = persistence_service or StorageFactory.create()
        self.llm_client = llm_client or LLMClient()
        self.event_bus = event_bus or EventBus.get_instance()

    def _generate_request_id(self) -> str:
        return f"req-{uuid.uuid4().hex[:12]}"

    def _generate_call_id(self) -> str:
        return f"call-{uuid.uuid4().hex[:12]}"

    def execute(self, session_id: str, model_config_id: str, messages: List[Dict],
               stream: bool = False, model_name: str = None, api_type: str = None,
               api_address: str = None, api_key: str = None, temperature: float = 0.7,
               max_tokens: int = 2000, tools: Optional[List[Dict]] = None) -> LLMExecutionResponse:
        request_id = self._generate_request_id()
        dialog_id = session_id

        start_time = time.time()

        llm_request = LLMRequest(
            model_name=model_name or "default",
            messages=messages,
            api_type=api_type or "openai",
            api_address=api_address or "http://localhost/v1",
            api_key=api_key or "demo",
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools or []
        )

        try:
            # 发布LLM请求发送事件
            self.event_bus.publish(Event(
                event_type=EventTypes.LLM_REQUEST_SENT,
                payload={
                    'request_id': request_id,
                    'dialog_id': dialog_id,
                    'model_config_id': model_config_id,
                    'num_messages': len(messages),
                    'num_tools': len(tools) if tools else 0,
                    'stream': stream,
                    'source_component': 'L2_llm_execution',
                    'source_service': 'LLMExecutionService'
                }
            ))
            
            llm_response = self.llm_client.send_request(
                llm_request,
                session_id=dialog_id,
                model_config_id=model_config_id
            )
            
            # 发布LLM响应接收事件
            self.event_bus.publish(Event(
                event_type=EventTypes.LLM_RESPONSE_RECEIVED,
                payload={
                    'request_id': request_id,
                    'dialog_id': dialog_id,
                    'has_content': bool(llm_response.content),
                    'has_tool_calls': bool(hasattr(llm_response, 'tool_calls') and llm_response.tool_calls),
                    'source_component': 'L2_llm_execution',
                    'source_service': 'LLMExecutionService'
                }
            ))

            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)

            content = llm_response.content or ""
            finish_reason = llm_response.finish_reason or "stop"
            tool_calls = None

            if hasattr(llm_response, 'tool_calls'):
                tool_calls = llm_response.tool_calls
                if tool_calls is None:
                    tool_calls = []

            usage = {}
            if hasattr(llm_response, 'usage') and llm_response.usage:
                usage = llm_response.usage

            response = LLMExecutionResponse(
                request_id=request_id,
                dialog_id=dialog_id,
                content=content,
                finish_reason=finish_reason,
                tool_calls=tool_calls,
                usage=usage,
                status="completed"
            )

            call_record = LLMCallRecord(
                call_id=self._generate_call_id(),
                dialog_id=dialog_id,
                model_config_id=model_config_id,
                request=llm_request.to_dict(),
                response={
                    'content': content,
                    'finish_reason': finish_reason,
                    'tool_calls': tool_calls,
                    'usage': usage
                },
                status="completed",
                duration_ms=duration_ms
            )
            self._save_call_record(call_record)

            self.event_bus.publish(Event(
                event_type=EventTypes.LLM_CALL_COMPLETED,
                payload={
                    'request_id': request_id,
                    'dialog_id': dialog_id,
                    'duration_ms': duration_ms,
                    'source_component': 'L2_llm_execution',
                    'source_service': 'LLMExecutionService'
                }
            ))

            return response

        except Exception as e:
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)

            call_record = LLMCallRecord(
                call_id=self._generate_call_id(),
                dialog_id=dialog_id,
                model_config_id=model_config_id,
                request=llm_request.to_dict(),
                response={'error': str(e)},
                status="failed",
                duration_ms=duration_ms
            )
            self._save_call_record(call_record)

            self.event_bus.publish(Event(
                event_type=EventTypes.LLM_CALL_FAILED,
                payload={
                    'request_id': request_id,
                    'dialog_id': dialog_id,
                    'error': str(e)
                }
            ))

            return LLMExecutionResponse(
                request_id=request_id,
                dialog_id=dialog_id,
                content=f"Error: {str(e)}",
                finish_reason="error",
                status="failed"
            )

    def execute_stream(self, session_id: str, model_config_id: str,
                      messages: List[Dict], on_chunk: Callable,
                      model_name: str = None, api_type: str = None,
                      api_address: str = None, api_key: str = None,
                      temperature: float = 0.7, max_tokens: int = 2000) -> LLMExecutionResponse:
        request_id = self._generate_request_id()
        dialog_id = session_id

        llm_request = LLMRequest(
            model_name=model_name or "default",
            messages=messages,
            api_type=api_type or "openai",
            api_address=api_address or "http://localhost/v1",
            api_key=api_key or "demo",
            temperature=temperature,
            max_tokens=max_tokens
        )

        collected_content = []
        start_time = time.time()

        try:
            for chunk in self.llm_client.send_request_stream(llm_request, session_id=dialog_id):
                if chunk:
                    delta = chunk.get('delta', '')
                    collected_content.append(delta)
                    on_chunk(chunk)

            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)

            content = ''.join(collected_content)

            response = LLMExecutionResponse(
                request_id=request_id,
                dialog_id=dialog_id,
                content=content,
                finish_reason="stop",
                status="completed"
            )

            call_record = LLMCallRecord(
                call_id=self._generate_call_id(),
                dialog_id=dialog_id,
                model_config_id=model_config_id,
                request=llm_request.to_dict(),
                response={'content': content, 'finish_reason': 'stop'},
                status="completed",
                duration_ms=duration_ms
            )
            self._save_call_record(call_record)

            return response

        except Exception as e:
            call_record = LLMCallRecord(
                call_id=self._generate_call_id(),
                dialog_id=dialog_id,
                model_config_id=model_config_id,
                request=llm_request.to_dict(),
                response={'error': str(e)},
                status="failed"
            )
            self._save_call_record(call_record)

            return LLMExecutionResponse(
                request_id=request_id,
                dialog_id=dialog_id,
                content=f"Error: {str(e)}",
                finish_reason="error",
                status="failed"
            )

    def parse_tool_calls(self, content: str) -> List[Dict]:
        tool_calls = []

        if 'tool_calls' in content:
            try:
                import json
                import re

                json_match = re.search(r'\[.*?\]', content, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    if isinstance(parsed, list):
                        for item in parsed:
                            if isinstance(item, dict) and 'tool_name' in item:
                                tool_calls.append(item)
            except:
                pass

        return tool_calls

    def _save_call_record(self, record: LLMCallRecord):
        self.persistence.save('llm_calls', record.to_dict())

    def get_call_record(self, call_id: str) -> Optional[LLMCallRecord]:
        all_records = self.persistence.list('llm_calls')
        for r in all_records:
            if r.get('call_id') == call_id:
                return LLMCallRecord.from_dict(r)
        return None

    def list_call_records(self, dialog_id: str = None, limit: int = 100) -> List[LLMCallRecord]:
        all_records = self.persistence.list('llm_calls')
        result = [LLMCallRecord.from_dict(r) for r in all_records]

        if dialog_id:
            result = [r for r in result if r.dialog_id == dialog_id]

        result.sort(key=lambda x: x.created_at, reverse=True)
        return result[:limit]


def get_llm_execution_service() -> LLMExecutionService:
    return LLMExecutionService()
